"""
LoreForge API methods — conversation management and streaming chat.
Imported by AppAPI via mixin pattern.
"""
import json
import uuid
import queue
from datetime import datetime
from pathlib import Path

LORE_SYSTEM_PROMPT = """You are LoreForge, a creative world-building and quest design assistant for Asheron's Call private server administrators using ACEmulator.

Your expertise covers:

ASHERON'S CALL LORE & WORLD
- Dereth: geography, history, the Empyrean civilization, the Olthoi invasion, the Shadows
- Playable races: Aluvian, Gharundim, Sho, Viamontian — their cultures, tensions, and histories
- Major factions: Society of the Radiant Blood, Celestial Hand, Eldrytch Web, and others
- Key figures: Asheron, Bael'Zharon, Gaerlan, the Hopeslayer, Elysa Strathelar
- Iconic locations: Arwic, Holtburg, Shoushi, Yaraq, the Direlands, Aerlinthe
- Game events: the War of Blood, the Hopeslayer's release, Martine's Betrayal

PRIVATE SERVER DESIGN
- Custom quest chains: pacing, rewards, NPC dialogue flows, kill tasks
- Server identity: creating cohesive lore that extends or diverges from canon
- Content tiering: progression balance, difficulty curves, WCID range planning
- NPC personality and dialogue: making characters feel authentic to the AC world
- World events, seasonal content, raid encounters, and campaign storylines

HOW YOU HELP
- Ask clarifying questions to understand the user's server vision
- Suggest narrative hooks, plot twists, faction dynamics, and lore connections
- Help draft NPC dialogue, quest descriptions, and item lore text
- Point out potential lore conflicts with canon when relevant
- Think through player experience: discovery, immersion, pacing

Keep responses focused and conversational. Ask one good question at a time when gathering information. Be creative but grounded in what makes Asheron's Call feel authentic."""


class LoreMixin:
    """Mixed into AppAPI to provide LoreForge conversation management."""

    def _ensure_lore_queue(self):
        if not hasattr(self, '_lore_queue'):
            self._lore_queue = queue.Queue()
        if not hasattr(self, '_lore_generating'):
            self._lore_generating = False

    # ── Conversation management ───────────────────────────────────────────────

    def list_conversations(self) -> dict:
        try:
            self._ensure_lore_queue()
            convos = []
            lore_dir = self.config.lore_dir
            for f in sorted(lore_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    convos.append({
                        "id":      data.get("id", f.stem),
                        "name":    data.get("name", "Untitled"),
                        "updated": data.get("updated", ""),
                        "count":   len(data.get("messages", [])),
                    })
                except Exception:
                    pass
            return {"success": True, "conversations": convos}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_conversation(self, convo_id: str) -> dict:
        try:
            f = self.config.lore_dir / f"{convo_id}.json"
            if not f.exists():
                return {"success": False, "error": "Not found"}
            data = json.loads(f.read_text(encoding="utf-8"))
            return {"success": True, "conversation": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def new_conversation(self, name: str) -> dict:
        try:
            cid = uuid.uuid4().hex[:12]
            now = datetime.utcnow().isoformat()
            data = {"id": cid, "name": name or "New Conversation",
                    "created": now, "updated": now, "messages": []}
            f = self.config.lore_dir / f"{cid}.json"
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"success": True, "conversation": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename_conversation(self, convo_id: str, name: str) -> dict:
        try:
            f = self.config.lore_dir / f"{convo_id}.json"
            data = json.loads(f.read_text(encoding="utf-8"))
            data["name"] = name
            data["updated"] = datetime.utcnow().isoformat()
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_conversation(self, convo_id: str) -> dict:
        try:
            f = self.config.lore_dir / f"{convo_id}.json"
            if f.exists():
                f.unlink()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_conversation_messages(self, convo_id: str, messages: list) -> dict:
        try:
            f = self.config.lore_dir / f"{convo_id}.json"
            data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"id": convo_id, "name": "Untitled", "created": datetime.utcnow().isoformat()}
            data["messages"] = messages
            data["updated"] = datetime.utcnow().isoformat()
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Streaming chat ────────────────────────────────────────────────────────

    def lore_chat(self, convo_id: str, messages: list, server_identity_context: str = '') -> dict:
        """Start streaming a LoreForge response. Poll with poll_lore()."""
        self._ensure_lore_queue()
        if self._lore_generating:
            return {"success": False, "error": "Already generating"}
        # No API-key gate here: ACEForge now operates exclusively against a
        # local Ollama instance (the cloud-provider picker was removed from
        # Settings), and the API client already substitutes a placeholder
        # key for Ollama since it ignores authentication entirely. This also
        # avoids getting stuck for any existing install whose saved config
        # still has a stale pre-Ollama-only provider value.

        self._lore_generating = True
        while not self._lore_queue.empty():
            try: self._lore_queue.get_nowait()
            except: break

        self.api_client.update_credentials(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
        )

        import threading
        def on_chunk(text):
            self._lore_queue.put({"type": "chunk", "text": text})
        def on_done(text):
            self._lore_generating = False
            self._lore_queue.put({"type": "done"})
        def on_error(msg):
            self._lore_generating = False
            self._lore_queue.put({"type": "error", "message": msg})

        try:
            # Build dynamic system prompt — base + server identity context
            system_prompt = LORE_SYSTEM_PROMPT
            if server_identity_context:
                system_prompt = LORE_SYSTEM_PROMPT + server_identity_context
            threading.Thread(
                target=self.api_client.stream_generate,
                args=(system_prompt, self._build_lore_prompt(messages),
                      on_chunk, on_done, on_error),
                daemon=True,
            ).start()
        except Exception as e:
            self._lore_generating = False
            return {"success": False, "error": str(e)}

        return {"success": True}

    def _build_lore_prompt(self, messages: list) -> str:
        """Convert conversation history to a single prompt string."""
        parts = []
        for m in messages[:-1]:  # all but last (which is the new user message)
            role = "User" if m["role"] == "user" else "Assistant"
            parts.append(f"{role}: {m['content']}")
        if messages:
            parts.append(f"User: {messages[-1]['content']}")
        return "\n\n".join(parts)

    def poll_lore(self) -> dict:
        """Poll for LoreForge streaming chunks."""
        self._ensure_lore_queue()
        items = []
        try:
            while True:
                items.append(self._lore_queue.get_nowait())
        except queue.Empty:
            pass
        return {"items": items, "generating": self._lore_generating}

    def stop_lore(self) -> dict:
        self._ensure_lore_queue()
        self._lore_generating = False
        self._lore_queue.put({"type": "done"})
        return {"success": True}
