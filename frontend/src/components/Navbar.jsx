// File: src/components/Navbar.jsx

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu } from "lucide-react"

export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  // Toggle login state (for demo/testing only)
  const toggleLogin = () => {
    setIsLoggedIn(!isLoggedIn)
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo/Brand */}
        <motion.div
          className="flex items-center gap-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          {/* Logo placeholder - replace with your actual logo */}
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
            AW
          </div>
          <span className="text-lg font-bold">MindEase</span>
        </motion.div>

        {/* Desktop navigation */}
        <nav className="hidden md:flex items-center gap-6">
          <motion.a
            href="#"
            className="text-sm font-medium hover:text-primary transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Home
          </motion.a>
          <motion.a
            href="#"
            className="text-sm font-medium hover:text-primary transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Features
          </motion.a>
          <motion.a
            href="#"
            className="text-sm font-medium hover:text-primary transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Contact
          </motion.a>
        </nav>

        {/* Right-side Auth Actions (Desktop) */}
        <div className="hidden md:flex items-center gap-4">
          {/* Reserve space to avoid shifting: we use a min-w to match the widest possible content (logout vs. two buttons) */}
          <div className="flex items-center gap-2 min-w-[180px] justify-end">
            {isLoggedIn ? (
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button onClick={toggleLogin}>Logout</Button>
              </motion.div>
            ) : (
              <>
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button onClick={() => alert("Sign In logic here")}>Sign In</Button>
                </motion.div>
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button variant="outline" onClick={() => alert("Register logic here")}>Register</Button>
                </motion.div>
              </>
            )}
          </div>
        </div>

        {/* Mobile Menu */}
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right">
            <div className="flex flex-col gap-6 mt-6">
              <a href="#" className="text-sm font-medium hover:text-primary transition-colors">
                Home
              </a>
              <a href="#" className="text-sm font-medium hover:text-primary transition-colors">
                Features
              </a>
              <a href="#" className="text-sm font-medium hover:text-primary transition-colors">
                Contact
              </a>

              {/* Auth Buttons for mobile */}
              {isLoggedIn ? (
                <Button onClick={toggleLogin} className="mt-4">
                  Logout
                </Button>
              ) : (
                <div className="flex flex-col gap-2 mt-4">
                  <Button onClick={() => alert("Sign In logic here")}>Sign In</Button>
                  <Button variant="outline" onClick={() => alert("Register logic here")}>Register</Button>
                </div>
              )}
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  )
}
