import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { EyeIcon, EyeOffIcon, BrainCircuit } from "lucide-react"
import { Link } from "react-router-dom" // Assuming you're using React Router

export default function Login() {
  // State for form inputs
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { type: "spring", stiffness: 100 },
    },
  }

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault()
    console.log("Login submitted:", { username, password })
    // Add your authentication logic here
  }

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      {/* Left side - Project content */}
      <motion.div
        className="w-full md:w-1/2 bg-gradient-to-br from-blue-600 to-purple-700 text-white p-8 md:p-12 flex flex-col justify-center"
        initial={{ x: -50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-md mx-auto">
          <motion.div
            className="flex items-center mb-6"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <BrainCircuit className="h-10 w-10 mr-2" />
            <h1 className="text-3xl font-bold">AI Emotional Wellbeing</h1>
          </motion.div>

          <motion.h2
            className="text-2xl md:text-4xl font-bold mb-6"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            Welcome Back
          </motion.h2>

          <motion.p
            className="text-lg mb-8 opacity-90"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            Your AI companion for emotional wellbeing is ready to support you. Log in to continue your journey toward
            better mental health.
          </motion.p>

          <motion.div
            className="space-y-4"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.5 }}
          >
            <div className="flex items-center">
              <div className="h-1 w-1 rounded-full bg-white mr-2"></div>
              <p>Real-time emotion detection and analysis</p>
            </div>
            <div className="flex items-center">
              <div className="h-1 w-1 rounded-full bg-white mr-2"></div>
              <p>Personalized support during moments of distress</p>
            </div>
            <div className="flex items-center">
              <div className="h-1 w-1 rounded-full bg-white mr-2"></div>
              <p>Adaptive relaxation techniques and music therapy</p>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Right side - Login form */}
      <motion.div
        className="w-full md:w-1/2 bg-white dark:bg-gray-950 p-8 md:p-12 flex items-center justify-center"
        initial={{ x: 50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="w-full max-w-md">
          <motion.div
            className="mb-8 text-center"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <h2 className="text-3xl font-bold mb-2">Login</h2>
            <p className="text-gray-500 dark:text-gray-400">Sign in to access your AI emotional wellbeing companion</p>
          </motion.div>

          <motion.form
            onSubmit={handleSubmit}
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-6"
          >
            {/* Username input */}
            <motion.div variants={itemVariants}>
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="h-12"
                />
              </div>
            </motion.div>

            {/* Password input */}
            <motion.div variants={itemVariants}>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="h-12 pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                  >
                    {showPassword ? <EyeOffIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            </motion.div>

            {/* Forgot password link */}
            <motion.div variants={itemVariants} className="text-right">
              <Link
                to="/forgot-password"
                className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Forgot password?
              </Link>
            </motion.div>

            {/* Login button */}
            <motion.div variants={itemVariants}>
              <Button type="submit" className="w-full h-12 text-base">
                Login
              </Button>
            </motion.div>

            {/* Sign up link */}
            <motion.div variants={itemVariants} className="text-center mt-6">
              <p className="text-gray-600 dark:text-gray-400">
                Don't have an account?{" "}
                <Link
                  to="/signup"
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                >
                  Sign up
                </Link>
              </p>
            </motion.div>
          </motion.form>
        </div>
      </motion.div>
    </div>
  )
}

