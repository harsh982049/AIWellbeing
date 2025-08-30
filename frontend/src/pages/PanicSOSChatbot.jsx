import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import Picker from "@emoji-mart/react"
import { Smile } from "lucide-react"
import Navbar from "@/components/Navbar"
import Footer from "@/components/Footer"

const API_BASE = "http://127.0.0.1:5000"

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

const PanicSOSChatbot = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content: "Hello! I'm here to help you through any panic or anxiety you might be experiencing. How are you feeling right now?",
      sender: "bot",
    },
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState("")
  const scrollAreaRef = useRef(null)
  const emojiPickerRef = useRef(null)
  const sessionIdRef = useRef(getOrCreateSessionId())
  const eventSourceRef = useRef(null)

  // auto-scroll
  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (viewport) {
        setTimeout(() => {
          viewport.scrollTop = viewport.scrollHeight
        }, 30)
      }
    }
  }, [messages])

  // close SSE on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  const startStream = (userText) => {
    // create a placeholder bot message that we'll append tokens to
    const typingId = Date.now() + 1
    setMessages((prev) => [
      ...prev,
      { id: typingId, content: "", sender: "bot", typing: true },
    ])

    // Build SSE URL with query params
    const url = new URL(`${API_BASE}/api/chatbot/stream`)
    url.searchParams.set("session_id", sessionIdRef.current)
    url.searchParams.set("message", userText)

    // Start EventSource
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onmessage = (e) => {
      if (!e?.data) return
      if (e.data === "[DONE]") {
        // finalize
        setMessages((prev) => prev.map((m) => m.id === typingId ? { ...m, typing: false } : m))
        es.close()
        eventSourceRef.current = null
        setIsSending(false)
        return
      }

      try {
        const payload = JSON.parse(e.data)
        if (payload.error) {
          throw new Error(payload.error)
        }
        const token = payload.token || ""
        // append token to the in-flight bot message
        setMessages((prev) =>
          prev.map((m) =>
            m.id === typingId ? { ...m, content: (m.content || "") + token } : m
          )
        )
      } catch (err) {
        // if a chunk isn't JSON (shouldn't happen), ignore
        console.error("SSE parse error:", err)
      }
    }

    es.onerror = (err) => {
      console.error("SSE error", err)
      setError("Connection lost while streaming. Please try again.")
      // convert the typing bubble to a static error message
      setMessages((prev) =>
        prev.map((m) =>
          m.id === typingId ? { ...m, typing: false, content: (m.content || "") + "\n[stream ended]" } : m
        )
      )
      es.close()
      eventSourceRef.current = null
      setIsSending(false)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    setError("")
    const text = inputMessage.trim()
    if (!text || isSending) return

    // push user message
    const userMsg = { id: Date.now(), content: text, sender: "user" }
    setMessages((prev) => [...prev, userMsg])
    setInputMessage("")
    setIsSending(true)

    // stream response
    startStream(text)
  }

  const handleEmojiSelect = (emoji) => {
    setInputMessage((prev) => prev + emoji.native)
    setShowEmojiPicker(false)
  }

  const resetConversation = async () => {
    setError("")
    setIsSending(true)
    try {
      await axios.post(`${API_BASE}/api/chatbot/reset`, {
        session_id: sessionIdRef.current,
      })
      setMessages([
        {
          id: 1,
          content:
            "Hello! I'm here to help you through any panic or anxiety you might be experiencing. How are you feeling right now?",
          sender: "bot",
        },
      ])
    } catch (e) {
      setError("Could not reset the conversation. Please try again.")
    } finally {
      setIsSending(false)
    }
  }

  return (
    <>
      <Navbar />
      <motion.div
        className="container mx-auto px-4 py-8 max-w-2xl"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-2xl font-bold text-primary">Panic SOS Chatbot</CardTitle>
            <Button variant="secondary" size="sm" onClick={resetConversation} disabled={isSending}>
              Reset
            </Button>
          </CardHeader>

          <CardContent>
            <ScrollArea className="h-[280px] pr-4" ref={scrollAreaRef}>
              <AnimatePresence initial={false}>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"} mb-4`}
                  >
                    <div className={`flex items-end ${message.sender === "user" ? "flex-row-reverse" : "flex-row"}`}>
                      <Avatar className={`w-8 h-8 ${message.sender === "user" ? "ml-2" : "mr-2"}`}>
                        <AvatarFallback>{message.sender === "user" ? "U" : "B"}</AvatarFallback>
                      </Avatar>
                      <div
                        className={`px-4 py-2 rounded-lg ${
                          message.sender === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        } whitespace-pre-wrap`}
                      >
                        {message.content || (message.typing ? "…" : "")}
                      </div>
                    </div>
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
                    <Picker onEmojiSelect={handleEmojiSelect} />
                  </div>
                )}
              </div>

              <Input
                type="text"
                placeholder="Type your message here..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                className="flex-grow"
                disabled={isSending}
              />

              <Button type="submit" disabled={isSending || !inputMessage.trim()}>
                {isSending ? "Sending..." : "Send"}
              </Button>
            </form>
          </CardFooter>
        </Card>
      </motion.div>
      <Footer />
    </>
  )
}

export default PanicSOSChatbot
