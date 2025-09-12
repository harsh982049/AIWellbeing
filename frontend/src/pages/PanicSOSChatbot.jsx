// src/pages/PanicSOSChatbot.jsx
import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Picker from "@emoji-mart/react"
import { Smile, Trash2, Plus } from "lucide-react"

import { api, API_BASE, getToken } from "@/lib/api"
import ChatMessage from "@/components/ChatMessage"
import ChatSidebar from "@/components/ChatSidebar"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import Navbar from "@/components/Navbar"
import Footer from "@/components/Footer"

const ACTIVE_KEY = "active_chat_id"

// ---------- Helpers ----------
function getOrCreateSessionId() {
  let id = localStorage.getItem("chatbot_session_id")
  if (!id) {
    const bytes = new Uint8Array(16)
    crypto.getRandomValues(bytes)
    bytes[6] = (bytes[6] & 0x0f) | 0x40
    bytes[8] = (bytes[8] & 0x3f) | 0x80
    id = [...bytes].map((b, i) => {
      const s = b.toString(16).padStart(2, "0")
      return [4, 6, 8, 10].includes(i) ? "-" + s : s
    }).join("")
    localStorage.setItem("chatbot_session_id", id)
  }
  return id
}

// Stream SSE via fetch so we can send Authorization header (EventSource cannot)
async function streamSSE({ url, headers = {}, onToken, onError, onDone }) {
  try {
    const res = await fetch(url, { headers })
    if (!res.ok || !res.body) {
      throw new Error(`HTTP ${res.status}`)
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder("utf-8")
    let buf = ""

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      // Parse SSE: chunks end with \n\n, lines start with "data: "
      let idx
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const chunk = buf.slice(0, idx).trim()
        buf = buf.slice(idx + 2)
        if (!chunk) continue
        const line = chunk.split("\n").find(l => l.startsWith("data: "))
        if (!line) continue
        const payloadStr = line.slice(6)
        if (payloadStr === "[DONE]") {
          onDone?.()
          return
        }
        try {
          const payload = JSON.parse(payloadStr)
          if (payload.error) onError?.(new Error(payload.error))
          const token = payload.token || ""
          if (token) onToken?.(token)
        } catch {
          // ignore malformed lines
        }
      }
    }
    onDone?.()
  } catch (e) {
    onError?.(e)
  }
}

export default function PanicSOSChatbot() {
  const [messages, setMessages] = useState([
    { id: 1, role: "ai", content: "Hello! I'm here to help you through any panic or anxiety you might be experiencing. How are you feeling right now?" },
  ])

  const [inputMessage, setInputMessage] = useState("")
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState("")
  const [activeChatId, setActiveChatId] = useState(() => {
    const cached = localStorage.getItem(ACTIVE_KEY)
    return cached ? Number(cached) : null
  })
  const [isAuthed, setIsAuthed] = useState(!!getToken())

  const scrollAreaRef = useRef(null)
  const emojiPickerRef = useRef(null)
  const sessionIdRef = useRef(getOrCreateSessionId())
  const typingMsgIdRef = useRef(null)

  // ---------- Auto-scroll ----------
  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (viewport) setTimeout(() => { viewport.scrollTop = viewport.scrollHeight }, 30)
    }
  }, [messages])

  // ---------- Load/ensure chat (JWT) or stick to session mode ----------
  useEffect(() => {
    async function ensureChat() {
      if (!isAuthed) return
      try {
        // 1) Load list
        const { data: list } = await api.get("/api/chats")
        const chats = list?.chats || []

        // Helper to load messages into UI
        const loadMessages = async (chatId) => {
          const { data: hist } = await api.get(`/api/chats/${chatId}/messages?limit=100`)
          const loaded = (hist?.messages || []).map((m) => ({
            id: m.id,
            role: m.role === "human" ? "user" : "ai",
            content: m.content,
          }))
          setMessages(loaded.length ? loaded : [
            { id: 1, role: "ai", content: "How are you feeling right now?" },
          ])
        }

        // 2) If we had a cached chat id and it still exists, use it
        if (activeChatId && chats.some(c => c.chat_id === activeChatId)) {
          setActiveChatId(activeChatId)
          localStorage.setItem(ACTIVE_KEY, String(activeChatId))
          await loadMessages(activeChatId)
          return
        }

        // 3) Else, try to reuse latest EMPTY normal chat
        const normals = chats.filter(c => !c.is_journal)
        if (normals.length) {
          const candidate = normals[0] // list is ordered newest first by backend
          // Check if empty
          const { data: peek } = await api.get(`/api/chats/${candidate.chat_id}/messages?limit=1`)
          const isEmpty = !peek?.messages?.length
          if (isEmpty) {
            setActiveChatId(candidate.chat_id)
            localStorage.setItem(ACTIVE_KEY, String(candidate.chat_id))
            await loadMessages(candidate.chat_id)
            return
          }
        }

        // 4) Otherwise, create a new normal chat
        const { data } = await api.post("/api/chats", { is_journal: false })
        setActiveChatId(data.chat_id)
        localStorage.setItem(ACTIVE_KEY, String(data.chat_id))
        setMessages([
          { id: 1, role: "ai", content: "New conversation started. How are you feeling right now?" },
        ])
      } catch {
        // Fallback to guest mode if anything fails
        setIsAuthed(false)
      }
    }
    ensureChat()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Persist active chat id whenever it changes
  useEffect(() => {
    if (activeChatId) {
      localStorage.setItem(ACTIVE_KEY, String(activeChatId))
    }
  }, [activeChatId])

  // ---------- Compose helpers ----------
  const addTypingBubble = () => {
    const id = Date.now() + 1
    typingMsgIdRef.current = id
    setMessages((prev) => [...prev, { id, role: "ai", content: "", typing: true }])
    return id
  }
  const appendToken = (id, token) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, content: (m.content || "") + token } : m)))
  }
  const finalizeTyping = (id) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, typing: false } : m)))
  }

  // ---------- Send ----------
  const handleSendMessage = async (e) => {
    e.preventDefault()
    setError("")
    const text = inputMessage.trim()
    if (!text || isSending) return

    // push user message locally
    const userMsg = { id: Date.now(), role: "user", content: text }
    setMessages((prev) => [...prev, userMsg])
    setInputMessage("")
    setIsSending(true)

    // add typing bubble
    const typingId = addTypingBubble()

    try {
      if (isAuthed && activeChatId) {
        // JWT mode (persistent): stream with headers via fetch
        const qs = new URLSearchParams({
          chat_id: String(activeChatId),
          message: text,
        })
        const url = `${API_BASE}/api/chatbot/stream?${qs.toString()}`
        const token = getToken() || ""

        await streamSSE({
          url,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          onToken: (tok) => appendToken(typingId, tok),
          onError: (err) => setError(err.message || "Stream error"),
          onDone: () => finalizeTyping(typingId),
        })
      } else {
        // Session mode (guest): still stream, but pass session_id
        const qs = new URLSearchParams({
          session_id: sessionIdRef.current,
          message: text,
        })
        const url = `${API_BASE}/api/chatbot/stream?${qs.toString()}`
        await streamSSE({
          url,
          onToken: (tok) => appendToken(typingId, tok),
          onError: (err) => setError(err.message || "Stream error"),
          onDone: () => finalizeTyping(typingId),
        })
      }
    } catch (err) {
      setError(err?.message || "Sorry, I’m having trouble responding right now.")
      finalizeTyping(typingId)
    } finally {
      setIsSending(false)
    }
  }

  // ---------- Header actions ----------
  const handleNewChat = async () => {
    if (!isAuthed) return
    try {
      const { data } = await api.post("/api/chats", { is_journal: false })
      setActiveChatId(data.chat_id)
      localStorage.setItem(ACTIVE_KEY, String(data.chat_id))
      setMessages([
        { id: 1, role: "ai", content: "New conversation started. How are you feeling right now?" },
      ])
    } catch {
      setError("Could not start a new chat.")
    }
  }

  const handleDeleteChat = async () => {
    if (!isAuthed || !activeChatId) return
    if (!confirm("Delete this chat and its data? This cannot be undone.")) return
    try {
      await api.delete(`/api/chats/${activeChatId}`)
      // after delete: clear active and reload list via sidebar selecting another
      setActiveChatId(null)
      localStorage.removeItem(ACTIVE_KEY)
      setMessages([
        { id: 1, role: "ai", content: "How are you feeling right now?" },
      ])
    } catch {
      setError("Could not delete chat.")
    }
  }

  // ---------- Reset (guest only) ----------
  const resetConversation = async () => {
    if (isAuthed && activeChatId) {
      await handleNewChat()
      return
    }

    // Guest: ephemeral reset (existing endpoint)
    setError("")
    setIsSending(true)
    try {
      await api.post("/api/chatbot/reset", { session_id: sessionIdRef.current })
      setMessages([
        { id: 1, role: "ai", content: "Hello! I'm here to help. How are you feeling right now?" },
      ])
    } catch {
      setError("Could not reset the conversation. Please try again.")
    } finally {
      setIsSending(false)
    }
  }

  // ---------- UI ----------
  return (
    <>
      <Navbar />
      <motion.div
        className="container mx-auto px-4 py-8 max-w-5xl"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="grid grid-cols-1 md:grid-cols-[16rem_1fr] gap-4">
          {/* Sidebar only when logged in */}
          {isAuthed ? (
            <ChatSidebar
              activeChatId={activeChatId}
              onSelect={async (id) => {
                setError("")
                if (!id) {
                  // nothing selected yet, leave messages as-is
                  setActiveChatId(null)
                  localStorage.removeItem(ACTIVE_KEY)
                  return
                }
                setActiveChatId(id)
                localStorage.setItem(ACTIVE_KEY, String(id))
                try {
                  const { data } = await api.get(`/api/chats/${id}/messages?limit=100`)
                  const loaded = (data?.messages || []).map((m) => ({
                    id: m.id, role: m.role === "human" ? "user" : "ai", content: m.content
                  }))
                  setMessages(loaded.length ? loaded : [
                    { id: 1, role: "ai", content: "How are you feeling right now?" },
                  ])
                } catch {
                  setError("Could not load messages.")
                }
              }}
              className="h-full"
            />
          ) : (
            <div className="hidden md:block" />
          )}

          {/* Chat card */}
          <Card className="w-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-2xl font-bold text-primary">
                Panic SOS Chatbot
                {!isAuthed && <span className="ml-2 text-xs text-muted-foreground">(guest)</span>}
              </CardTitle>

              <div className="flex gap-2">
                {isAuthed && (
                  <>
                    <Button variant="outline" size="sm" onClick={handleNewChat} title="New chat">
                      <Plus className="h-4 w-4 mr-1" /> New
                    </Button>
                    {activeChatId && (
                      <Button variant="destructive" size="sm" onClick={handleDeleteChat} title="Delete this chat">
                        <Trash2 className="h-4 w-4 mr-1" /> Delete
                      </Button>
                    )}
                  </>
                )}
                <Button variant="secondary" size="sm" onClick={resetConversation} disabled={isSending}>
                  {isAuthed ? "Reset (new)" : "Reset"}
                </Button>
              </div>
            </CardHeader>

            <CardContent>
              <ScrollArea className="h-[420px] pr-4" ref={scrollAreaRef}>
                <AnimatePresence initial={false}>
                  {messages.map((m) => (
                    <motion.div
                      key={m.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.25 }}
                    >
                      <ChatMessage role={m.role} content={m.content} typing={m.typing} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </ScrollArea>
              {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
            </CardContent>

            <CardFooter>
              <form onSubmit={handleSendMessage} className="flex w-full gap-2">
                <div className="relative">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                    disabled={isSending}
                  >
                    <Smile className="h-5 w-5" />
                  </Button>
                  {showEmojiPicker && (
                    <div
                      ref={emojiPickerRef}
                      className="absolute bottom-full mb-2 left-0 bg-white shadow-lg rounded-lg z-50"
                    >
                      <Picker onEmojiSelect={(emoji) => {
                        setInputMessage((prev) => prev + emoji.native)
                        setShowEmojiPicker(false)
                      }} />
                    </div>
                  )}
                </div>

                <Input
                  type="text"
                  placeholder="Type your message here…"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  className="flex-grow"
                  disabled={isSending}
                />

                <Button type="submit" disabled={isSending || !inputMessage.trim()}>
                  {isSending ? "Sending…" : "Send"}
                </Button>
              </form>
            </CardFooter>
          </Card>
        </div>
      </motion.div>
      <Footer />
    </>
  )
}
