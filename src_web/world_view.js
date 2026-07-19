/* ===========================================================================
 * WorldForge — visual landblock placement editor
 * ---------------------------------------------------------------------------
 * SOURCE FILE — lives in src_web/, which is NOT bundled into the app. It is
 * inlined into index.html by build_world_view.py; the packaged app does not
 * reliably serve sibling .js, so never load it with a <script src>.
 * Edit here, then run:  python build_world_view.py
 *
 * Terrain comes from client_cell_1.dat via aceforge/landblock_dat.py and
 * arrives as base64 typed arrays. Clicking it writes a landblock_instance row
 * through aceforge/landblock.py. Coordinates are landblock-local metres, Z up
 * (AC convention), x and y both 0..192.
 * ======================================================================== */

var WV = {
  ready:false, gl:null, scene:null, camera:null, renderer:null, raycaster:null,
  terrain:null, markers:[], ghost:null, ghostOn:false,
  // 'terrain' shows the outdoor surface; 'dungeon' shows interior cell floors.
  // They are different coordinate spaces, so only one is ever in the scene.
  view:'terrain', floors:null, edgeLines:null, cells:[],
  // Interior visibility. Rooms are closed shells, so seeing in means dropping
  // ceilings and/or isolating a storey. -1 = all levels.
  level:-1, cutaway:0.6, roomIndex:null, triLevel:null, triKind:null, triHeight:null,
  atlasTex:null, atlasPending:false, terrainGain:1.9,
  landblock:null, data:null, weenies:[], selectedWcid:null, selectedName:'',
  heading:0, status:'', busy:false,
  // camera orbit state, in AC world space (Z up)
  target:{x:96,y:96,z:0}, dist:260, yaw:-0.9, pitch:0.85,
  drag:null, lastPick:null, selectedGuid:null
};

var WV_SIZE = 192;

/* ── feature gate ────────────────────────────────────────────────────────── */
//
// WorldForge ships hidden while it's in development so releases cut for
// unrelated fixes don't expose it. The whole feature is still present in the
// binary — only the tab is withheld — so it can be exercised in place rather
// than needing a separate build.

/** Show or hide the tab from the persisted config. */
function worldApplyVisibility(){
  var btn = document.getElementById('worldTabBtn');
  if(!btn) return;
  worldApi('world_is_enabled').then(function(r){
    var on = !!(r && r.enabled);
    btn.style.display = on ? '' : 'none';
    // If it's switched off while in use, don't strand the user on a dead panel.
    if(!on && document.getElementById('worldWS').classList.contains('active')){
      var first = document.querySelector('.mode-tab');
      if(first) switchMode('manual', first);
    }
  }).catch(function(){ /* no bridge (dev/browser) — stay hidden */ });
}

/** Toggle the tab and persist it. Bound to Ctrl+Alt+W. */
function worldToggleEnabled(){
  var btn = document.getElementById('worldTabBtn');
  var currentlyOn = !!btn && btn.style.display !== 'none';
  worldApi('world_set_enabled', !currentlyOn).then(function(r){
    if(r && r.error){ console.warn('[WorldForge] '+r.error); return; }
    var on = !!(r && r.enabled);
    if(btn) btn.style.display = on ? '' : 'none';
    if(on){
      if(btn) switchMode('world', btn);
    } else if(document.getElementById('worldWS').classList.contains('active')){
      var first = document.querySelector('.mode-tab');
      if(first) switchMode('manual', first);
    }
    console.log('[WorldForge] tab ' + (on ? 'shown' : 'hidden'));
  }).catch(function(e){ console.warn('[WorldForge] toggle failed: '+(e&&e.message||e)); });
}

// Registered at parse time so the chord works before the tab exists.
// Ctrl+Alt+W rather than Ctrl+Shift+W, which the webview host may intercept
// as a window-close shortcut.
window.addEventListener('keydown', function(e){
  if(e.ctrlKey && e.altKey && !e.shiftKey && (e.key === 'w' || e.key === 'W')){
    e.preventDefault();
    worldToggleEnabled();
  }
});

// The bridge attaches asynchronously; ask once it's there. The timeout covers
// browser/dev mode, where no bridge ever arrives and the tab stays hidden.
window.addEventListener('pywebviewready', worldApplyVisibility);
if(window.pywebview && window.pywebview.api && window.pywebview.api.world_is_enabled){
  worldApplyVisibility();
} else {
  setTimeout(worldApplyVisibility, 1400);
}

/* ── boot ───────────────────────────────────────────────────────────────── */

function worldInit(){
  if(WV.ready){ worldRefreshStatus(); return; }
  var host = document.getElementById('worldCanvasWrap');
  if(!host) return;
  if(typeof THREE === 'undefined'){
    worldSetMsg('3D library failed to load — the World editor is unavailable.', true);
    return;
  }
  try{ worldBuildScene(host); }
  catch(e){ worldSetMsg('WebGL init failed: '+(e&&e.message||e), true); return; }
  WV.ready = true;
  worldRefreshStatus();
  worldRefreshDat();
  worldLoadAtlas();
  worldLoadWeenies();
}

function worldBuildScene(host){
  var w = host.clientWidth||900, h = host.clientHeight||600;

  WV.scene = new THREE.Scene();
  WV.scene.background = new THREE.Color(0x1d2026);

  WV.camera = new THREE.PerspectiveCamera(55, w/h, 0.5, 6000);
  WV.camera.up.set(0,0,1);                       // AC is Z-up

  WV.renderer = new THREE.WebGLRenderer({antialias:true});
  WV.renderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 2));
  WV.renderer.setSize(w,h);
  host.appendChild(WV.renderer.domElement);

  WV.scene.add(new THREE.AmbientLight(0xffffff, 0.62));
  var sun = new THREE.DirectionalLight(0xffffff, 0.85);
  sun.position.set(-140, -180, 320);
  WV.scene.add(sun);

  // Landblock footprint so the 192 m bounds stay obvious even on flat terrain.
  // Terrain view only: interiors are a different coordinate space and often
  // extend well past this box, so leaving it up just draws a stray rectangle.
  WV.footprint = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(WV_SIZE, WV_SIZE, 0.1)),
    new THREE.LineBasicMaterial({color:0x4a5568}));
  WV.footprint.position.set(WV_SIZE/2, WV_SIZE/2, 0);
  WV.scene.add(WV.footprint);

  WV.raycaster = new THREE.Raycaster();
  WV.ghost = worldMakeMarker(0xffcc33, 1.5);
  WV.ghost.visible = false;
  WV.scene.add(WV.ghost);

  worldBindInput(WV.renderer.domElement);
  window.addEventListener('resize', worldResize);
  worldUpdateCamera();
  worldRender();
}

function worldResize(){
  var host = document.getElementById('worldCanvasWrap');
  if(!host||!WV.renderer) return;
  var w = host.clientWidth||900, h = host.clientHeight||600;
  WV.camera.aspect = w/h; WV.camera.updateProjectionMatrix();
  WV.renderer.setSize(w,h);
  worldRender();
}

/* ── camera ─────────────────────────────────────────────────────────────── */

function worldUpdateCamera(){
  var cp = Math.max(0.05, Math.min(1.5, WV.pitch));
  WV.pitch = cp;
  WV.dist = Math.max(12, Math.min(1400, WV.dist));
  var r = WV.dist*Math.cos(cp);
  WV.camera.position.set(
    WV.target.x + r*Math.cos(WV.yaw),
    WV.target.y + r*Math.sin(WV.yaw),
    WV.target.z + WV.dist*Math.sin(cp));
  WV.camera.lookAt(WV.target.x, WV.target.y, WV.target.z);
}

function worldBindInput(cv){
  cv.addEventListener('contextmenu', function(e){ e.preventDefault(); });

  cv.addEventListener('mousedown', function(e){
    WV.drag = {x:e.clientX, y:e.clientY, btn:e.button, moved:0};
  });

  window.addEventListener('mouseup', function(e){
    if(!WV.drag) return;
    var d = WV.drag; WV.drag = null;
    // A click (not a drag) on the terrain places or selects.
    if(d.moved < 5 && d.btn === 0) worldClick(e);
  });

  window.addEventListener('mousemove', function(e){
    if(WV.drag){
      var dx = e.clientX-WV.drag.x, dy = e.clientY-WV.drag.y;
      WV.drag.moved += Math.abs(dx)+Math.abs(dy);
      WV.drag.x = e.clientX; WV.drag.y = e.clientY;
      if(WV.drag.btn === 0 && !e.shiftKey){
        WV.yaw   -= dx*0.006;
        WV.pitch += dy*0.006;
      } else {
        // pan across the ground plane, in view-aligned axes
        var s = WV.dist*0.0016;
        var cy = Math.cos(WV.yaw), sy = Math.sin(WV.yaw);
        WV.target.x += (-dx*(-sy) - dy*cy)*s;
        WV.target.y += (-dx*( cy) - dy*sy)*s;
      }
      worldUpdateCamera(); worldRender();
      return;
    }
    if(WV.ghostOn) worldHover(e);
  }, {passive:true});

  cv.addEventListener('wheel', function(e){
    e.preventDefault();
    WV.dist *= (e.deltaY>0 ? 1.12 : 0.89);
    worldUpdateCamera(); worldRender();
  }, {passive:false});
}

/* ── picking ────────────────────────────────────────────────────────────── */

function worldPick(e){
  var target = worldPickTarget();
  if(!target) return null;
  var r = WV.renderer.domElement.getBoundingClientRect();
  var m = new THREE.Vector2(
    ((e.clientX-r.left)/r.width)*2-1,
    -((e.clientY-r.top)/r.height)*2+1);
  WV.raycaster.setFromCamera(m, WV.camera);
  var hit = WV.raycaster.intersectObject(target, false);
  if(!hit.length) return null;
  var p = hit[0].point;
  if(WV.view==='dungeon'){
    // Interior coords are the cell frame's own space — no 0-192 clamp.
    var f = worldFrameAt(p);
    return {x:p.x, y:p.y, z:p.z, frame:f,
            cellHint:f ? (f.cellCount===1 ? f.cells[0]
                                          : f.cellCount+' cells here') : null};
  }
  return {x:Math.max(0,Math.min(WV_SIZE,p.x)),
          y:Math.max(0,Math.min(WV_SIZE,p.y)),
          z:p.z, cell:0, cellHex:'0x0000'};
}

function worldHover(e){
  var p = worldPick(e);
  WV.lastPick = p;
  if(!p){ WV.ghost.visible=false; worldRender(); return; }
  WV.ghost.visible = true;
  WV.ghost.position.set(p.x, p.y, p.z);
  var el = document.getElementById('worldCoords');
  if(el) el.textContent = p.x.toFixed(2)+', '+p.y.toFixed(2)+'  z '+p.z.toFixed(2)+
    (p.cellHint ? '  ['+p.cellHint+']' : '');
  worldRender();
}

function worldClick(e){
  var p = worldPick(e);
  if(!p) return;
  if(WV.view === 'dungeon'){
    if(WV.moveMode && WV.selectedGuid){ worldMoveSelectedTo(p); return; }
    // With room geometry we can shortlist which cell a point is in. It's a
    // shortlist, not an answer, so the cell is always shown before writing.
    if(WV.ghostOn && WV.selectedWcid && WV.hasRooms){ worldPlaceIndoor(p); return; }
    worldSelectNearest(p);
    return;
  }
  if(WV.ghostOn && WV.selectedWcid){ worldPlaceAt(p); return; }
  worldSelectNearest(p);
}

function worldSelectNearest(p){
  var best=null, bd=1e9;
  WV.markers.forEach(function(m){
    var d = Math.pow(m.position.x-p.x,2)+Math.pow(m.position.y-p.y,2)
          + Math.pow(m.position.z-p.z,2);
    if(d<bd){ bd=d; best=m; }
  });
  WV.selectedGuid = (best && bd < 64) ? best.userData.guid : null;
  if(WV.selectedGuid){
    worldSetMsg('Selected '+best.userData.name+' ('+best.userData.wcid+')'+
      (WV.view==='dungeon' ? ' — MOVE HERE repositions it inside its own cell.' : ''));
  }
  worldRenderInstanceList();
  worldRender();
}

/** Reposition the selected row, keeping its existing obj_Cell_Id. */
function worldMoveSelectedTo(p){
  if(WV.busy || !WV.selectedGuid) return;
  WV.busy = true;
  worldApi('world_move', {
    landblock: WV.landblock, guid: WV.selectedGuid,
    x: p.x, y: p.y, z: p.z, heading: WV.heading
  }).then(function(r){
    WV.busy = false;
    if(r.error){ worldSetMsg(r.error, true); return; }
    worldSetMoveMode(false);
    worldSetMsg('Moved '+r.guid+' to '+r.x.toFixed(2)+', '+r.y.toFixed(2)+
                ', '+r.z.toFixed(2)+'  →  '+r.reloadCommand);
    worldReloadInstances();
  }).catch(function(e){ WV.busy=false; worldSetMsg(String(e.message||e), true); });
}

/**
 * Indoor placement: resolve candidate cells, then confirm before writing.
 *
 * Cell membership can't be derived from a position — measured on 11,198 retail
 * rows, a single candidate is still the wrong cell 6% of the time and 23% of
 * points match nothing. So we never auto-assign silently: one candidate is
 * confirmed, several opens a picker, none refuses.
 */
function worldPlaceIndoor(p){
  if(WV.busy) return;
  WV.busy = true;
  worldSetMsg('Resolving cell…');
  worldApi('world_resolve_cell', {landblock:WV.landblock, x:p.x, y:p.y, z:p.z+0.3})
    .then(function(r){
      WV.busy = false;
      if(r.error){ worldSetMsg(r.error, true); return; }
      if(!r.candidates.length){
        worldSetMsg('That point is not inside any interior cell — click inside a room.', true);
        return;
      }
      WV.pendingPlace = {x:p.x, y:p.y, z:p.z};
      if(r.candidates.length === 1) worldConfirmIndoor(r.candidates[0]);
      else worldShowCellPicker(r.candidates);
    })
    .catch(function(e){ WV.busy=false; worldSetMsg(String(e.message||e), true); });
}

function worldShowCellPicker(cands){
  var el = document.getElementById('worldCellPicker');
  if(!el) return;
  el.style.display = 'block';
  el.innerHTML = '<div style="font-size:9px;font-weight:700;letter-spacing:.08em;'+
    'color:var(--ink-dim);margin-bottom:4px">'+cands.length+' CELLS OVERLAP HERE — PICK ONE</div>'+
    cands.map(function(c,i){
      return '<div onclick=\'worldConfirmIndoor('+JSON.stringify(c)+')\' '+
        'style="padding:4px 6px;cursor:pointer;font-size:11px;'+
        'font-family:JetBrains Mono,monospace;border-bottom:1px solid var(--border-lt)'+
        (i===0?';background:var(--parch-dk)':'')+'">'+
        c.objCellId+'<span style="color:var(--ink-dim)"> env '+c.envId+
        ' · depth '+c.depth.toFixed(2)+(i===0?' · best':'')+'</span></div>';
    }).join('')+
    '<div onclick="worldCancelIndoor()" style="padding:4px 6px;cursor:pointer;'+
    'font-size:10px;color:var(--ink-dim);text-align:center">cancel</div>';
}

function worldCancelIndoor(){
  WV.pendingPlace = null;
  var el = document.getElementById('worldCellPicker');
  if(el){ el.style.display='none'; el.innerHTML=''; }
  worldSetMsg('Placement cancelled.');
}

function worldConfirmIndoor(cand){
  var p = WV.pendingPlace;
  var el = document.getElementById('worldCellPicker');
  if(el){ el.style.display='none'; el.innerHTML=''; }
  if(!p){ return; }
  WV.pendingPlace = null;
  WV.busy = true;
  worldApi('world_place', {
    landblock: WV.landblock, wcid: WV.selectedWcid,
    x: p.x, y: p.y, z: p.z, cell: cand.cell,
    heading: WV.heading, name: WV.selectedName
  }).then(function(r){
    WV.busy = false;
    if(r.error){ worldSetMsg(r.error, true); return; }
    worldSetMsg('Placed '+r.guidHex+' in cell '+cand.objCellId+' at '+
      r.x.toFixed(2)+', '+r.y.toFixed(2)+', '+r.z.toFixed(2)+
      (r.created?' — created '+WV.landblock+'.sql':'')+'  →  '+r.reloadCommand);
    worldReloadInstances();
  }).catch(function(e){ WV.busy=false; worldSetMsg(String(e.message||e), true); });
}

function worldSetMoveMode(on){
  WV.moveMode = !!on && !!WV.selectedGuid;
  var b = document.getElementById('worldMoveBtn');
  if(b){
    b.style.background = WV.moveMode ? 'var(--crimson)' : 'none';
    b.style.color = WV.moveMode ? '#fff' : 'var(--ink-dim)';
  }
  if(WV.moveMode) worldSetMsg('Click a floor to move the selected placement there.');
}

function worldToggleMove(){
  if(!WV.selectedGuid){ worldSetMsg('Select a placement first.', true); return; }
  worldSetMoveMode(!WV.moveMode);
}

/* ── geometry ───────────────────────────────────────────────────────────── */

function worldB64Bytes(str){
  var bin = atob(str), n = bin.length, bytes = new Uint8Array(n);
  for(var i=0;i<n;i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

function worldB64(str, Ctor){
  return new Ctor(worldB64Bytes(str));
}

/* ── terrain texturing ───────────────────────────────────────────────────── */

/**
 * Blend the three corner terrain types across each triangle.
 *
 * Every vertex carries the same triple of corner types plus its own barycentric
 * weight, so the interpolated weight tells each fragment how much of each corner
 * texture it should get — the same soft transition the client shows, rather than
 * a hard edge at every cell boundary.
 *
 * Tiles are addressed by fract(uv), which has a discontinuity at tile seams and
 * would confuse mipmap derivative selection, so the atlas is sampled with
 * LinearFilter and no mipmaps.
 */
var WORLD_TERRAIN_VS = [
  'attribute vec3 aTypes;',
  'attribute vec3 aWeights;',
  'varying vec3 vTypes;',
  'varying vec3 vWeights;',
  'varying vec2 vUv2;',
  'varying vec3 vNrm;',
  'void main(){',
  '  vTypes = aTypes; vWeights = aWeights; vUv2 = uv;',
  '  vNrm = normalize(normalMatrix * normal);',
  '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
  '}'
].join('\n');

var WORLD_TERRAIN_FS = [
  'uniform sampler2D uAtlas;',
  'uniform vec2 uGrid;',
  'uniform vec3 uLight;',
  'uniform float uAmbient;',
  'uniform float uGain;',
  'varying vec3 vTypes;',
  'varying vec3 vWeights;',
  'varying vec2 vUv2;',
  'varying vec3 vNrm;',
  'vec3 tile(float t, vec2 uv){',
  '  float c = mod(t, uGrid.x);',
  '  float r = floor(t / uGrid.x);',
  '  vec2 sz = vec2(1.0) / uGrid;',
  // Inset a half-texel so neighbouring tiles cannot bleed across the seam.
  '  vec2 f = clamp(fract(uv), 0.01, 0.99);',
  '  return texture2D(uAtlas, (vec2(c, r) + f) * sz).rgb;',
  '}',
  'void main(){',
  '  vec3 w = vWeights / max(vWeights.x + vWeights.y + vWeights.z, 0.0001);',
  '  vec3 col = tile(vTypes.x, vUv2) * w.x',
  '           + tile(vTypes.y, vUv2) * w.y',
  '           + tile(vTypes.z, vUv2) * w.z;',
  '  float d = max(dot(normalize(vNrm), normalize(uLight)), 0.0);',
  // AC's terrain textures are dark diffuse maps the client brightens at render
  // time; shown raw they read as mud. uGain restores a legible surface.
  '  vec3 lit = col * uGain * (uAmbient + (1.0 - uAmbient) * d);',
  '  gl_FragColor = vec4(min(lit, vec3(1.0)), 1.0);',
  '}'
].join('\n');

function worldTerrainMaterial(mesh){
  // No atlas yet (still loading, or Pillow missing) — flat vertex colours.
  if(!WV.atlasTex) return new THREE.MeshLambertMaterial({
    vertexColors:true, side:THREE.DoubleSide });
  return new THREE.ShaderMaterial({
    uniforms:{
      uAtlas:{value:WV.atlasTex},
      uGrid:{value:new THREE.Vector2(mesh.atlasCols||8, mesh.atlasRows||4)},
      uLight:{value:new THREE.Vector3(-0.35,-0.45,0.82)},
      uAmbient:{value:0.65},
      uGain:{value:WV.terrainGain}
    },
    vertexShader:WORLD_TERRAIN_VS,
    fragmentShader:WORLD_TERRAIN_FS,
    side:THREE.DoubleSide
  });
}

function worldLoadAtlas(){
  if(WV.atlasTex || WV.atlasPending) return;
  WV.atlasPending = true;
  worldApi('world_terrain_atlas').then(function(r){
    WV.atlasPending = false;
    if(r.error){ console.warn('[WorldForge] terrain atlas: '+r.error); return; }
    var img = new Image();
    img.onload = function(){
      var tex = new THREE.Texture(img);
      tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
      tex.minFilter = THREE.LinearFilter;      // fract() addressing breaks mips
      tex.magFilter = THREE.LinearFilter;
      tex.generateMipmaps = false;
      // The sheet is authored with terrain type 0 in the TOP-LEFT tile and the
      // shader indexes rows downward, so the default vertical flip would map
      // row 0 to the bottom — every type would sample the wrong tile (type 3
      // landed on BlueIce, tinting the whole world blue).
      tex.flipY = false;
      tex.needsUpdate = true;
      WV.atlasTex = tex;
      // Re-skin terrain already on screen.
      if(WV.terrain && WV.data){
        WV.terrain.material.dispose();
        WV.terrain.material = worldTerrainMaterial(WV.data.mesh);
        worldRender();
      }
    };
    img.onerror = function(){
      WV.atlasFailed = true;
      console.warn('[WorldForge] terrain atlas image failed to decode');
    };
    img.src = 'data:image/png;base64,' + r.png;
  }).catch(function(e){
    // Don't swallow this. The bridge may not be ready when the panel first
    // initialises; worldLoad() retries, so record the reason and move on.
    WV.atlasPending = false;
    console.warn('[WorldForge] terrain atlas unavailable: ' + (e && e.message || e));
  });
}

function worldBuildTerrain(mesh){
  if(WV.terrain){
    WV.scene.remove(WV.terrain);
    WV.terrain.geometry.dispose(); WV.terrain.material.dispose();
    WV.terrain = null;
  }
  var g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(worldB64(mesh.positions, Float32Array), 3));
  g.setAttribute('normal',   new THREE.BufferAttribute(worldB64(mesh.normals,   Float32Array), 3));
  g.setAttribute('color',    new THREE.BufferAttribute(worldB64(mesh.colors,    Float32Array), 3));
  if(mesh.uvs)     g.setAttribute('uv',       new THREE.BufferAttribute(worldB64(mesh.uvs,     Float32Array), 2));
  if(mesh.types)   g.setAttribute('aTypes',   new THREE.BufferAttribute(worldB64(mesh.types,   Float32Array), 3));
  if(mesh.weights) g.setAttribute('aWeights', new THREE.BufferAttribute(worldB64(mesh.weights, Float32Array), 3));
  g.setIndex(new THREE.BufferAttribute(worldB64(mesh.indices, Uint32Array), 1));
  g.computeBoundingSphere();
  WV.terrain = new THREE.Mesh(g, worldTerrainMaterial(mesh));
  WV.scene.add(WV.terrain);
}

/* ── dungeon (interior cells) ────────────────────────────────────────────── */

function worldClearDungeon(){
  [WV.floors, WV.edgeLines].forEach(function(o){
    if(!o) return;
    WV.scene.remove(o); o.geometry.dispose(); o.material.dispose();
  });
  WV.floors = null; WV.edgeLines = null;
}

function worldBuildDungeon(d){
  worldClearDungeon();
  WV.cells = d.frames || [];
  WV.hasRooms = !!d.triangleCount;          // real geometry vs box placeholders
  if(!d.triangleCount && !d.cellCount) return;

  var g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(worldB64(d.positions, Float32Array), 3));
  g.setAttribute('normal',   new THREE.BufferAttribute(worldB64(d.normals,   Float32Array), 3));
  g.setAttribute('color',    new THREE.BufferAttribute(worldB64(d.colors,    Float32Array), 3));
  // Keep the full index; visibility filtering rewrites it in place rather than
  // rebuilding vertex buffers, so toggling a storey is instant.
  WV.roomIndex = worldB64(d.indices, Uint32Array);
  WV.triLevel  = d.triLevel  ? new Uint8Array(worldB64Bytes(d.triLevel))  : null;
  WV.triKind   = d.triKind   ? new Uint8Array(worldB64Bytes(d.triKind))   : null;
  WV.triHeight = d.triHeight ? new Uint8Array(worldB64Bytes(d.triHeight)) : null;
  g.setIndex(new THREE.BufferAttribute(WV.roomIndex.slice(), 1));
  g.computeBoundingSphere();
  WV.floors = new THREE.Mesh(g, new THREE.MeshLambertMaterial({
    vertexColors:true, side:THREE.DoubleSide }));
  WV.scene.add(WV.floors);
  worldApplyRoomFilter();

  // Box outlines exist only for the placeholder mesh — real room geometry
  // carries its own walls, so there is nothing to imply.
  if(d.edges && d.edges.length){
    var eg = new THREE.BufferGeometry();
    eg.setAttribute('position', new THREE.BufferAttribute(worldB64(d.edges, Float32Array), 3));
    WV.edgeLines = new THREE.LineSegments(eg, new THREE.LineBasicMaterial({
      color:0x8fa0b8, transparent:true, opacity:0.30 }));
    WV.scene.add(WV.edgeLines);
  }
}

var ENVCELL_H = 6.0;

/**
 * Rebuild the room index for the current storey and cutaway height.
 *
 * The cutaway slices each cell by height rather than hiding "ceiling" triangles,
 * because a vaulted or domed roof is not horizontal and never classifies as one
 * — in retail 0007's town network only 134 of ~2,400 triangles read as flat
 * ceilings while the rest of the roof registers as wall. Slicing by height is
 * shape-agnostic and takes the upper walls with it, which is what you want when
 * looking down into a room.
 *
 * Filtering rewrites the index in place against one vertex buffer, so changing
 * storey or cutaway is instant.
 */
function worldApplyRoomFilter(){
  if(!WV.floors || !WV.roomIndex) return;
  var src = WV.roomIndex, lv = WV.triLevel, ht = WV.triHeight;
  var cut = Math.round(WV.cutaway * 255);
  var out = new Uint32Array(src.length), n = 0;
  for(var t=0; t<src.length/3; t++){
    if(ht && WV.cutaway < 1 && ht[t] > cut) continue;
    if(lv && WV.level>=0 && lv[t]!==WV.level) continue;
    out[n++]=src[t*3]; out[n++]=src[t*3+1]; out[n++]=src[t*3+2];
  }
  WV.floors.geometry.setIndex(new THREE.BufferAttribute(out.slice(0,n), 1));
  WV.floors.geometry.computeBoundingSphere();
  if(WV.data) worldBuildMarkers(WV.data.instances);
  worldUpdateLevelButtons();
  worldRender();
}

/**
 * Which storey an instance stands on: the highest floor at or below it.
 *
 * Not a +/- window around each floor — storeys are 6 m apart and the tolerance
 * needed for objects resting slightly below their floor makes neighbouring
 * windows overlap, which double-counts every object near a boundary.
 */
function worldInstanceStorey(inst){
  var levels = WV.data ? (WV.data.dungeon.levels||[]) : [];
  var best = -1;
  for(var i=0;i<levels.length;i++) if(inst.z >= levels[i] - 1.0) best = i;
  return best;
}

/** Is an instance on the storey currently being shown? */
function worldInstanceVisible(inst){
  if(WV.view!=='dungeon' || WV.level<0 || !WV.data) return true;
  return worldInstanceStorey(inst) === WV.level;
}

function worldSetLevel(i){
  WV.level = i;
  worldApplyRoomFilter();
  var levels = WV.data ? (WV.data.dungeon.levels||[]) : [];
  worldSetMsg(i<0 ? 'Showing all storeys.'
                  : 'Storey '+(i+1)+' of '+levels.length+' (z '+levels[i].toFixed(1)+').');
}

function worldSetCutaway(v){
  WV.cutaway = Math.max(0.15, Math.min(1, parseFloat(v)||0.6));
  worldApplyRoomFilter();
  var lab = document.getElementById('worldCutawayVal');
  if(lab) lab.textContent = WV.cutaway>=1 ? 'whole' : Math.round(WV.cutaway*100)+'%';
}

function worldUpdateLevelButtons(){
  var host = document.getElementById('worldLevels');
  if(!host) return;
  var levels = WV.data ? (WV.data.dungeon.levels||[]) : [];
  if(WV.view!=='dungeon' || !levels.length || !WV.hasRooms){
    host.style.display='none'; return;
  }
  host.style.display='block';
  var btn = function(label, active, onclick, title){
    return '<button onclick="'+onclick+'" title="'+(title||'')+'" style="padding:3px 7px;'+
      'font-family:var(--ui-font);font-size:9px;font-weight:700;letter-spacing:.06em;'+
      'cursor:pointer;border:1px solid var(--border);margin:0 3px 3px 0;'+
      (active?'background:var(--crimson);color:#fff':'background:none;color:var(--ink-dim)')+
      '">'+label+'</button>';
  };
  var html = '<div style="font-family:var(--ui-font);font-size:9px;font-weight:700;'+
    'letter-spacing:.08em;color:var(--ink-dim);margin-bottom:3px">STOREY</div>';
  html += btn('ALL', WV.level<0, 'worldSetLevel(-1)');
  for(var i=0;i<levels.length;i++)
    html += btn(String(i+1), WV.level===i, 'worldSetLevel('+i+')', 'z '+levels[i].toFixed(1));
  html += '<div style="display:flex;align-items:center;gap:6px;margin-top:4px">'+
    '<span style="font-family:var(--ui-font);font-size:9px;font-weight:700;'+
    'letter-spacing:.08em;color:var(--ink-dim)">CUTAWAY</span>'+
    '<input type="range" min="0.15" max="1" step="0.05" value="'+WV.cutaway+'" '+
    'oninput="worldSetCutaway(this.value)" title="Hide everything above this '+
    'fraction of each room height" style="flex:1">'+
    '<span id="worldCutawayVal" style="font-family:JetBrains Mono,monospace;'+
    'font-size:10px;color:var(--ink-mid);width:38px;text-align:right">'+
    (WV.cutaway>=1?'whole':Math.round(WV.cutaway*100)+'%')+'</span></div>';
  host.innerHTML = html;
}

/**
 * Nearest interior frame to a point.
 *
 * Returns the *location*, not a cell id. A frame is shared by up to 28 cells,
 * so which cell a point belongs to cannot be inferred from position alone —
 * that needs the Environment geometry. Used for readout only, never to build
 * an obj_Cell_Id.
 */
function worldFrameAt(p){
  var best=null, bd=1e18;
  for(var i=0;i<WV.cells.length;i++){
    var c=WV.cells[i];
    var dz=(p.z-c.z);
    if(dz < -1 || dz > 7) continue;             // wrong storey
    var d=(c.x-p.x)*(c.x-p.x)+(c.y-p.y)*(c.y-p.y);
    if(d<bd){ bd=d; best=c; }
  }
  return (best && bd <= 64) ? best : null;
}

function worldSetView(mode){
  if(!WV.data) return;
  if(mode==='dungeon' && !WV.data.hasDungeon){
    worldSetMsg('This landblock has no interior cells.', true); return;
  }
  WV.view = mode;
  if(WV.terrain)   WV.terrain.visible   = (mode==='terrain');
  if(WV.footprint) WV.footprint.visible = (mode==='terrain');
  if(WV.floors)    WV.floors.visible    = (mode==='dungeon');
  if(WV.edgeLines) WV.edgeLines.visible = (mode==='dungeon');
  document.querySelectorAll('[data-worldview]').forEach(function(b){
    var on = b.getAttribute('data-worldview')===mode;
    b.style.background = on ? 'var(--crimson)' : 'none';
    b.style.color      = on ? '#fff' : 'var(--ink-dim)';
  });
  worldApplyRoomFilter();
  worldBuildMarkers(WV.data.instances);
  worldFrameView();
  worldSetPlaceMode(!!WV.selectedWcid);
  worldRenderInstanceList();
  worldRender();
}

/** Point the camera at whatever the active view actually occupies. */
function worldFrameView(){
  if(WV.view==='dungeon' && WV.data && WV.data.dungeon.cellCount){
    var b = WV.data.dungeon.bounds;
    WV.target = {x:(b.minX+b.maxX)/2, y:(b.minY+b.maxY)/2, z:(b.minZ+b.maxZ)/2};
    WV.dist = Math.max(60, Math.max(b.maxX-b.minX, b.maxY-b.minY) * 1.5);
  } else {
    var m = WV.data ? WV.data.mesh : null;
    WV.target = {x:WV_SIZE/2, y:WV_SIZE/2, z:m ? (m.minZ+m.maxZ)/2 : 0};
    WV.dist = 290;
  }
  WV.yaw = -0.9; WV.pitch = 0.85;
  worldUpdateCamera();
}

function worldMakeMarker(color, scale){
  var s = scale||1;
  var m = new THREE.Mesh(
    new THREE.ConeGeometry(1.7*s, 6.5*s, 6),
    new THREE.MeshLambertMaterial({color:color}));
  m.geometry.rotateX(Math.PI/2);            // point down the -Z axis
  m.geometry.translate(0,0,3.4*s);
  return m;
}

function worldBuildMarkers(instances){
  WV.markers.forEach(function(m){
    WV.scene.remove(m); m.geometry.dispose(); m.material.dispose();
  });
  WV.markers = [];
  var dungeon = (WV.view === 'dungeon');
  (instances||[]).forEach(function(inst){
    // Each view only shows the rows that live in its coordinate space, and in
    // the interior view only those on the storey currently displayed.
    if(dungeon ? !inst.inDungeon : !inst.placeable) return;
    if(dungeon && !worldInstanceVisible(inst)) return;
    var m = worldMakeMarker(inst.isLinkChild ? 0x62b0ff : 0xff5f56, 1);
    m.position.set(inst.x, inst.y, inst.z);
    m.userData = {guid:inst.guid, wcid:inst.wcid, name:inst.name};
    WV.scene.add(m); WV.markers.push(m);
  });
}

/** The mesh the active view raycasts against. */
function worldPickTarget(){
  return WV.view==='dungeon' ? WV.floors : WV.terrain;
}

function worldRender(){ if(WV.renderer) WV.renderer.render(WV.scene, WV.camera); }

/* ── data ───────────────────────────────────────────────────────────────── */

function worldApi(fn, arg){
  if(!window.pywebview || !window.pywebview.api || !window.pywebview.api[fn])
    return Promise.reject(new Error('Desktop app required'));
  return (arg === undefined) ? window.pywebview.api[fn]()
                             : window.pywebview.api[fn](arg);
}

function worldRefreshStatus(){
  worldApi('world_status').then(function(s){
    var el = document.getElementById('worldSetup');
    if(!el) return;
    if(s.error){ worldSetMsg(s.error, true); return; }
    var dirEl = document.getElementById('worldSqlDir');
    dirEl.textContent = s.sqlDir || '(not set)';
    dirEl.title = s.sqlDir || '';
    dirEl.style.color = s.sqlDirOk ? 'var(--ink-mid)' : 'var(--crimson)';

    // Say what the folder actually is. A folder full of weenie SQL looks fine
    // in the picker but holds no landblocks, and silently showing an empty
    // landblock gives the user nothing to act on.
    var why = document.getElementById('worldSqlDirWhy');
    if(why){
      why.textContent = s.sqlDirReason || '';
      why.style.color = s.sqlDirOk ? 'var(--ink-dim)' : 'var(--crimson)';
      if(s.sqlDirSuggestions && s.sqlDirSuggestions.length){
        why.textContent += ' — try: ' + s.sqlDirSuggestions[0];
      }
    }
    el.style.display = s.ready ? 'none' : 'block';
    if(!s.ready){
      var miss = [];
      if(!s.cellDatOk)  miss.push('client_cell_1.dat');
      if(!s.portalDatOk)miss.push('client_portal.dat');
      if(!s.sqlDirOk)   miss.push('landblock folder ('+(s.sqlDirReason||'not set')+')');
      worldSetMsg('Set up required: '+miss.join(', '), true);
    } else if(!WV.landblock){
      worldSetMsg('Ready — '+s.sqlDirCount+' landblock files. Enter a landblock '+
                  '(e.g. C6A9 for Arwic) and press Load.');
    }
  }).catch(function(e){ worldSetMsg(String(e.message||e), true); });
}

/**
 * Show which DAT set is loaded.
 *
 * Landblock/cell counts are the only practical way to tell sets apart — a
 * machine can hold several byte-identical copies of retail, while a custom set
 * built in ACME will differ in those totals.
 */
function worldRefreshDat(){
  worldApi('world_dat_info').then(function(d){
    var p = document.getElementById('worldDatPath');
    var i = document.getElementById('worldDatInfo');
    if(!p) return;
    if(d.error){ p.textContent='(error)'; if(i) i.textContent=d.error; return; }
    var path = d.folder || (d.cellDat||'').replace(/[\\/][^\\/]*$/, '');
    p.textContent = path || '(not found)';
    p.title = (d.cellDat||'') + '\n' + (d.portalDat||'');
    p.style.color = d.cells ? 'var(--ink-mid)' : 'var(--crimson)';
    if(i) i.textContent = d.cells
      ? d.landblocks.toLocaleString()+' landblocks · '+d.cells.toLocaleString()+
        ' interior cells · '+d.sizeMB+' MB'
      : 'client_cell_1.dat not readable';
  }).catch(function(){});
}

function worldBrowseDat(){
  worldApi('world_browse_dat_folder').then(function(r){
    if(!r || r.cancelled) return;
    if(r.error){ worldSetMsg(r.error, true); return; }
    worldRefreshDat();
    worldSetMsg('DAT set changed — '+r.landblocks.toLocaleString()+' landblocks, '+
                r.cells.toLocaleString()+' interior cells. Reload the landblock to apply.');
    // Cached geometry belongs to the old set; drop it.
    WV.data = null; WV.landblock = null;
    worldClearDungeon();
    if(document.getElementById('worldLbInput').value) worldLoad();
  }).catch(function(e){ worldSetMsg(String(e.message||e), true); });
}

function worldBrowseSqlDir(){
  worldApi('world_browse_sql_dir').then(function(r){
    if(!r || r.cancelled) return;
    if(r.error){ worldSetMsg(r.error, true); return; }
    worldRefreshStatus();
    if(r.ok){
      worldSetMsg('Landblock folder set — '+r.count+' landblock files found.');
      if(WV.landblock) worldLoad();
    } else {
      worldSetMsg('That folder has no landblock files: '+r.reason+
                  '. Look for a folder of 4-hex-digit .sql files '+
                  '(e.g. sql/landblocks, or 3-Core/6 LandBlockExtendedData/SQL).', true);
    }
  }).catch(function(e){ worldSetMsg(String(e.message||e), true); });
}

function worldLoadWeenies(){
  worldApi('world_list_weenies').then(function(r){
    if(r.error){ worldSetMsg(r.error, true); return; }
    WV.weenies = r.weenies||[];
    var sel = document.getElementById('worldWeenie');
    if(!sel) return;
    sel.innerHTML = '<option value="">— pick a weenie to place —</option>' +
      WV.weenies.map(function(w){
        return '<option value="'+w.wcid+'">'+w.wcid+' · '+
               String(w.name).replace(/</g,'&lt;')+'</option>';
      }).join('');
    if(!WV.weenies.length)
      sel.innerHTML = '<option value="">— no weenies found in your output folder —</option>';
  }).catch(function(){});
}

function worldOnWeenieChange(sel){
  WV.selectedWcid = sel.value ? parseInt(sel.value,10) : null;
  var w = WV.weenies.filter(function(x){ return x.wcid===WV.selectedWcid; })[0];
  WV.selectedName = w ? w.name : '';
  worldSetPlaceMode(!!WV.selectedWcid);
}

function worldSetPlaceMode(on){
  // Interiors are view/select/move only. Creating a row needs an obj_Cell_Id
  // and a click can't determine one — see worldFrameAt.
  var dungeon = (WV.view === 'dungeon');
  // Indoor placement needs room geometry to shortlist cells; without it the
  // view stays select/move/remove only.
  WV.ghostOn = on && !!WV.data && (!dungeon || WV.hasRooms);
  if(WV.ghost) WV.ghost.visible = false;
  var b = document.getElementById('worldPlaceHint');
  if(b){
    if(dungeon){
      b.style.display = 'block';
      b.style.borderLeftColor = WV.ghostOn ? '#ffcc33' : '#8fa0b8';
      b.textContent = WV.ghostOn
        ? 'Click inside a room to place. The cell is shown before anything is written.'
        : 'Interior view: select, move and remove existing placements.';
    } else {
      b.style.display = WV.ghostOn ? 'block' : 'none';
      b.style.borderLeftColor = '#ffcc33';
      b.textContent = 'Click the terrain to place. Z snaps to ground automatically.';
    }
  }
  worldRender();
}

function worldLoad(){
  var input = document.getElementById('worldLbInput');
  var lb = input ? input.value.trim() : '';
  if(!lb){ worldSetMsg('Enter a landblock id, e.g. C6A9', true); return; }
  worldSetMsg('Loading landblock '+lb+'…');
  // Retry the atlas here: worldInit may have fired before the js bridge was
  // ready, and terrain without it falls back to flat colours.
  worldLoadAtlas();
  worldApi('world_load_landblock', lb).then(function(d){
    if(d.error){ worldSetMsg(d.error, true); return; }
    WV.data = d; WV.landblock = d.landblockHex; WV.selectedGuid = null;
    worldBuildTerrain(d.mesh);
    worldBuildDungeon(d.dungeon);
    // Open on whichever view actually holds this landblock's content — most
    // server content is interior, so defaulting to terrain would usually show
    // an empty field.
    var wantDungeon = d.hasDungeon && d.dungeonCount > d.outdoorCount;
    var btn = document.getElementById('worldViewToggle');
    if(btn) btn.style.display = d.hasDungeon ? 'flex' : 'none';
    worldSetView(wantDungeon ? 'dungeon' : 'terrain');
    worldSetMsg('0x'+d.landblockHex+' loaded — '+d.outdoorCount+' outdoor, '+
      d.dungeonCount+' in '+d.envCellCount+' interior cells, '+
      d.staticObjects.length+' scenery. '+
      (d.sqlFileExists ? d.landblockHex+'.sql exists.'
                       : d.landblockHex+'.sql will be created on first placement.'));
  }).catch(function(e){ worldSetMsg(String(e.message||e), true); });
}

function worldPlaceAt(p){
  if(WV.busy) return;
  if(!WV.selectedWcid){ worldSetMsg('Pick a weenie first.', true); return; }
  var indoor = (WV.view === 'dungeon');
  if(indoor && p.cell == null){
    worldSetMsg('Click inside a cell — that spot is not in any interior cell.', true);
    return;
  }
  WV.busy = true;
  worldSetMsg('Placing '+WV.selectedWcid+'…');
  worldApi('world_place', {
    landblock: WV.landblock, wcid: WV.selectedWcid,
    x: p.x, y: p.y,
    // Outdoor snaps to terrain server-side; indoor has no terrain, so the
    // picked floor height is the Z.
    z: indoor ? p.z : null,
    cell: indoor ? p.cell : 0,
    heading: WV.heading, name: WV.selectedName
  }).then(function(r){
    WV.busy = false;
    if(r.error){ worldSetMsg(r.error, true); return; }
    worldSetMsg('Placed '+r.guidHex+' at '+r.x.toFixed(2)+', '+r.y.toFixed(2)+
      ', '+r.z.toFixed(2)+(r.created?' — created '+WV.landblock+'.sql':'')+
      '  →  '+r.reloadCommand);
    worldReloadInstances();
  }).catch(function(e){ WV.busy=false; worldSetMsg(String(e.message||e), true); });
}

function worldRemoveSelected(){
  if(!WV.selectedGuid){ worldSetMsg('Select a placement first.', true); return; }
  var guid = WV.selectedGuid;
  worldApi('world_remove', {landblock:WV.landblock, guid:guid}).then(function(r){
    if(r.error){ worldSetMsg(r.error, true); return; }
    WV.selectedGuid = null;
    worldSetMsg('Removed '+r.removed+'  →  '+r.reloadCommand);
    worldReloadInstances();
  }).catch(function(e){ worldSetMsg(String(e.message||e), true); });
}

function worldReloadInstances(){
  worldApi('world_load_landblock', WV.landblock).then(function(d){
    if(d.error) return;
    WV.data = d;
    worldBuildMarkers(d.instances);
    worldRenderInstanceList();
    worldRender();
  }).catch(function(){});
}

/* ── panel ──────────────────────────────────────────────────────────────── */

function worldSetMsg(text, isErr){
  var el = document.getElementById('worldMsg');
  if(!el) return;
  el.textContent = text;
  el.style.color = isErr ? 'var(--crimson)' : 'var(--ink-mid)';
}

function worldRenderInstanceList(){
  var el = document.getElementById('worldInstList');
  if(!el) return;
  var list = (WV.data && WV.data.instances) || [];
  if(!list.length){ el.innerHTML =
    '<div style="padding:10px;color:var(--ink-dim);font-size:11px">No placements in this landblock yet.</div>';
    return; }
  el.innerHTML = list.map(function(i){
    var sel = (i.guid === WV.selectedGuid);
    // Dim whatever the active view can't show, so the list matches the viewport.
    var shown = (WV.view==='dungeon') ? i.inDungeon : i.placeable;
    var tag = '';
    if(!i.outdoor) tag = i.inDungeon ? ' <span style="color:var(--ink-dim)">'+i.objCellId.slice(-4)+'</span>'
                                     : ' <span style="color:var(--crimson)">(cell missing)</span>';
    return '<div onclick="worldSelectGuid('+i.guid+')" style="padding:5px 8px;cursor:pointer;'+
      'border-bottom:1px solid var(--border-lt);font-size:11px;'+
      (sel?'background:var(--parch-dk);':'')+(shown?'':'opacity:.45;')+'">'+
      '<span style="font-family:JetBrains Mono,monospace;color:'+
        (shown?'var(--ink)':'var(--ink-dim)')+'">'+i.guidHex+'</span> '+
      '<span style="color:var(--ink-mid)">'+i.wcid+'</span> '+
      String(i.name||'').replace(/</g,'&lt;')+tag+
      '</div>';
  }).join('');
}

function worldSelectGuid(guid){
  WV.selectedGuid = guid;
  var inst = (WV.data.instances||[]).filter(function(i){return i.guid===guid;})[0];
  if(inst){
    // Selecting a row from the other view switches to it rather than doing
    // nothing — the list shows everything, both spaces.
    var want = inst.inDungeon ? 'dungeon' : (inst.placeable ? 'terrain' : null);
    if(want && want !== WV.view){ worldSetView(want); WV.selectedGuid = guid; }
    if(inst.inDungeon || inst.placeable){
      WV.target = {x:inst.x, y:inst.y, z:inst.z};
      WV.dist = Math.min(WV.dist, 60);
      worldUpdateCamera();
    }
  }
  worldRenderInstanceList();
  worldRender();
}

function worldSetHeading(v){
  WV.heading = parseFloat(v)||0;
  var el = document.getElementById('worldHeadingVal');
  if(el) el.textContent = WV.heading.toFixed(0)+'°';
}
