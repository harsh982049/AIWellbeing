import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu } from "lucide-react"

// Navbar component with responsive mobile menu
export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  // Toggle login state (for demo purposes)
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
          <span className="text-lg font-bold">AI Emotional Wellbeing</span>
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

        {/* Authentication button */}
        <div className="hidden md:flex items-center gap-4">
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button onClick={toggleLogin}>{isLoggedIn ? "Logout" : "Sign In / Register"}</Button>
          </motion.div>
        </div>

        {/* Mobile menu */}
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
              <Button onClick={toggleLogin} className="mt-4">
                {isLoggedIn ? "Logout" : "Sign In / Register"}
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  )
}

