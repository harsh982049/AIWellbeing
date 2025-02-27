import { motion } from "framer-motion"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, Shield, Music } from "lucide-react"

// Main Dashboard component
export default function Dashboard() {
  // Animation variants for staggered animations
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
      },
    },
  }

  // Features data
  const features = [
    {
      title: "Real-Time Emotion Detection",
      description:
        "Advanced AI algorithms detect and analyze your emotional state in real-time, providing personalized insights and recommendations.",
      icon: Brain,
      color: "bg-blue-100 dark:bg-blue-900",
    },
    {
      title: "Panic SOS with AI Companion",
      description:
        "Immediate support during moments of distress with our AI companion that guides you through proven calming techniques.",
      icon: Shield,
      color: "bg-purple-100 dark:bg-purple-900",
    },
    {
      title: "Adaptive Relaxation & Music Therapy",
      description:
        "Personalized relaxation exercises and music therapy that adapts to your emotional state and preferences.",
      icon: Music,
      color: "bg-green-100 dark:bg-green-900",
    },
  ]

  return (
    <div className="flex min-h-screen flex-col">
      {/* Navbar component */}
      <Navbar />

      {/* Main content */}
      <main className="flex-1">
        {/* Hero section with animation */}
        <motion.section
          className="bg-gradient-to-b from-blue-50 to-white dark:from-slate-900 dark:to-slate-800 py-16 md:py-24"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <motion.h1
                className="text-3xl md:text-5xl font-bold tracking-tighter"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
              >
                AI-Driven Emotional Wellbeing
              </motion.h1>
              <motion.p
                className="max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.5 }}
              >
                Harness the power of artificial intelligence to understand, manage, and improve your emotional
                wellbeing.
              </motion.p>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.5 }}
              >
                <Button size="lg" className="mt-4">
                  Get Started
                </Button>
              </motion.div>
            </div>
          </div>
        </motion.section>

        {/* Features section with staggered animation */}
        <section className="py-16 md:py-24">
          <div className="container px-4 md:px-6">
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-bold tracking-tighter mb-4">Key Features</h2>
              <p className="max-w-[700px] mx-auto text-gray-500 dark:text-gray-400">
                Our platform offers innovative tools to support your emotional health journey.
              </p>
            </motion.div>

            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {/* Map through features to create cards */}
              {features.map((feature, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="h-full transition-all duration-200 hover:shadow-lg">
                    <CardHeader>
                      <div className={`w-12 h-12 rounded-full ${feature.color} flex items-center justify-center mb-4`}>
                        <feature.icon className="h-6 w-6 text-primary" />
                      </div>
                      <CardTitle>{feature.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="text-base">{feature.description}</CardDescription>
                    </CardContent>
                    <CardFooter>
                      <Button variant="ghost" className="w-full">
                        Learn More
                      </Button>
                    </CardFooter>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Call to action section */}
        <motion.section
          className="bg-primary/5 py-16 md:py-24"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <h2 className="text-3xl font-bold tracking-tighter">Ready to Transform Your Emotional Wellbeing?</h2>
              <p className="max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400">
                Join thousands of users who have already improved their emotional health with our AI-powered platform.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mt-6">
                <Button size="lg">Sign Up Now</Button>
                <Button size="lg" variant="outline">
                  Learn More
                </Button>
              </div>
            </div>
          </div>
        </motion.section>
      </main>

      {/* Footer component */}
      <Footer />
    </div>
  )
}

