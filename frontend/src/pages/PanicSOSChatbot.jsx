import { useState, useRef, useEffect } from "react"
/* eslint-disable-next-line no-unused-vars */
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import Navbar from "@/components/Navbar"
import Footer from "@/components/Footer"

const PanicSOSChatbot = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            content: "Hello! I'm here to help you through any panic or anxiety you might be experiencing. How are you feeling right now?",
            sender: "bot",
        },
    ])
    const [inputMessage, setInputMessage] = useState("");
    const scrollAreaRef = useRef(null);
    // const messagesEndRef = useRef(null);

    // useEffect(() => {
    //     const lastMessage = scrollAreaRef.current.lastElementChild;
    //     if (lastMessage) {
    //         lastMessage.scrollIntoView({ behavior: "smooth", block: "end" });
    //     }
    // }, [messages]) // Updated dependency

    // This effect will handle scrolling within the ScrollArea component
    useEffect(() => {
        // Make sure we have access to the DOM and messages have been updated
        if (scrollAreaRef.current) {
            // Access the actual scroll viewport from the ScrollArea component
            const scrollViewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollViewport) {
                // Set the scroll position to the maximum possible value
                setTimeout(() => {
                    scrollViewport.scrollTop = scrollViewport.scrollHeight;
                }, 100); // Small delay to ensure content is rendered
            }
        }
    }, [messages]);

    // This function will handle scrolling to the bottom of messages
    // const scrollToBottom = () => {
    //     if (messagesEndRef.current) {
    //         messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    //     }
    // }
    
    // Scroll to bottom whenever messages change
    // useEffect(() => {
    //     scrollToBottom();
    // }, [messages]);

    const handleSendMessage = (e) => {
        e.preventDefault()
        if(inputMessage.trim() === "") return;

        const newUserMessage = {id: messages.length + 1, content: inputMessage, sender: "user"}
        setMessages([...messages, newUserMessage])

        // Simulate bot response
        setTimeout(() => {
        let botResponse;
            if(inputMessage.toLowerCase().includes("panic") || inputMessage.toLowerCase().includes("anxiety"))
            {
                botResponse = {
                    id: messages.length + 2,
                    content:
                        "I understand you're feeling anxious. Let's try a simple breathing exercise. Breathe in for 4 seconds, hold for 4 seconds, then exhale for 4 seconds. Repeat this 5 times. Would you like to try this together?",
                    sender: "bot",
                }
            }
            else if(inputMessage.toLowerCase().includes("yes") || inputMessage.toLowerCase().includes("okay"))
            {
                botResponse = {
                    id: messages.length + 2,
                    content:
                        "Great! Let's begin. Breathe in... 2... 3... 4... Hold... 2... 3... 4... Exhale... 2... 3... 4... Great job! Let's continue this for 4 more rounds.",
                    sender: "bot",
                }
            }
            else if(inputMessage.toLowerCase().includes("music") || inputMessage.toLowerCase().includes("relax"))
            {
                botResponse = {
                    id: messages.length + 2,
                    content:
                        "Music can be very soothing. I recommend listening to some calming nature sounds or soft instrumental music. Would you like me to suggest a playlist?",
                    sender: "bot",
                }
            }
            else
            {
                botResponse = {
                    id: messages.length + 2,
                    content:
                        "I'm here to support you. Remember, you're not alone in this. Would you like to try a breathing exercise or listen to some calming music?",
                    sender: "bot",
                }
            }
            setMessages((prevMessages) => [...prevMessages, botResponse]);
        }, 1000)

        setInputMessage("");
    }

    return (
        <>
            <Navbar/>

            <motion.div
            className="container mx-auto px-4 py-8 max-w-2xl"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            >
                <Card className="w-full">
                    <CardHeader>
                        <CardTitle className="text-2xl font-bold text-center text-primary">Panic SOS Chatbot</CardTitle>
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
                                    className={`px-4 py-2 rounded-lg ${message.sender === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}
                                    >
                                    {message.content}
                                    </div>
                                </div>
                                </motion.div>
                            ))}
                            </AnimatePresence>
                            {/* This is an empty div that we'll use as a reference to scroll to */}
                            {/* <div ref={messagesEndRef} /> */}
                        </ScrollArea>
                    </CardContent>
                    <CardFooter>
                        <form onSubmit={handleSendMessage} className="flex w-full gap-2">
                            <Input
                            type="text"
                            placeholder="Type your message here..."
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            className="flex-grow"
                            />
                            <Button type="submit">Send</Button>
                        </form>
                    </CardFooter>
                </Card>
            </motion.div>

            <Footer/>
        </>
    )
}

export default PanicSOSChatbot;

