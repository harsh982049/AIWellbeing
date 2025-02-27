import { motion } from "framer-motion"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"

// shadcn/ui imports
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"

// Icons
import { Brain, Shield, Music, Code, Book, Users } from "lucide-react"

// Animation variants
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

// Feature data
const features = [
  {
    title: "Real-Time Emotion Detection",
    description:
      "Experimental AI algorithms detect and analyze emotional states in real-time, demonstrating practical applications of machine learning in psychology.",
    icon: Brain,
    color: "bg-blue-100 dark:bg-blue-900",
  },
  {
    title: "Panic SOS with AI Companion",
    description:
      "A conceptual prototype showcasing how AI can provide guided interventions during moments of distress using evidence-based techniques.",
    icon: Shield,
    color: "bg-purple-100 dark:bg-purple-900",
  },
  {
    title: "Adaptive Relaxation & Music Therapy",
    description:
      "Explores the intersection of AI and sound therapy through personalized relaxation exercises for emotional regulation.",
    icon: Music,
    color: "bg-green-100 dark:bg-green-900",
  },
]

// Research topics
const researchTopics = [
  {
    title: "Implementation Architecture",
    count: "01",
    description: "Detailed documentation on system design, component integration, and technology stack choices."
  },
  {
    title: "Machine Learning Models",
    count: "02",
    description: "Analysis of ML algorithms employed for emotion detection, including data processing and accuracy evaluation."
  },
  {
    title: "User Experience Research",
    count: "03",
    description: "Findings from usability testing with student volunteers and proposed interface improvements."
  }
]

export default function Dashboard() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Navbar */}
      <Navbar />

      {/* Main content */}
      <main className="flex-1">
        {/* Hero Section */}
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
                AI-Driven Emotional Wellbeing Research
              </motion.h1>
              <motion.p
                className="max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.5 }}
              >
                A senior capstone project exploring the applications of artificial intelligence in understanding, 
                assessing, and supporting emotional wellbeing among college students.
              </motion.p>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.5 }}
              >
                <Button size="lg" className="mt-4">
                  View Project Overview
                </Button>
              </motion.div>
            </div>
          </div>
        </motion.section>

        {/* Features Section */}
        <section className="py-16 md:py-24">
          <div className="container px-4 md:px-6">
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-bold tracking-tighter mb-4">Project Modules</h2>
              <p className="max-w-[700px] mx-auto text-gray-500 dark:text-gray-400">
                Our research explores three interconnected approaches to AI-assisted emotional wellbeing.
              </p>
            </motion.div>

            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {features.map((feature, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="h-full transition-all duration-200 hover:shadow-lg">
                    <CardHeader>
                      <div
                        className={`w-12 h-12 rounded-full ${feature.color} flex items-center justify-center mb-4`}
                      >
                        <feature.icon className="h-6 w-6 text-primary" />
                      </div>
                      <CardTitle>{feature.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="text-base">{feature.description}</CardDescription>
                    </CardContent>
                    <CardFooter>
                      <Button variant="ghost" className="w-full">
                        See Research
                      </Button>
                    </CardFooter>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Technology Stack Section */}
        <section className="py-16 md:py-24 bg-primary/5">
          <div className="container px-4 md:px-6">
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-bold tracking-tighter mb-4">Technology Stack</h2>
              <p className="max-w-[700px] mx-auto text-gray-600 dark:text-gray-300">
                The project leverages multiple technologies to create a functional prototype.
              </p>
            </motion.div>

            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {/* Front-End */}
              <motion.div variants={itemVariants}>
                <Card className="h-full text-center">
                  <CardHeader>
                    <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mb-4">
                      <Code className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle>Front-End Development</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Built with React.js, Tailwind CSS, shadcn/ui components, and Framer Motion animations to create an accessible and responsive user interface.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>

              {/* ML/AI */}
              <motion.div variants={itemVariants}>
                <Card className="h-full text-center">
                  <CardHeader>
                    <div className="mx-auto w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center mb-4">
                      <Brain className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle>Machine Learning</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Implemented using TensorFlow and Python for emotion classification, reinforcement learning for adaptive responses, and natural language processing.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Backend */}
              <motion.div variants={itemVariants}>
                <Card className="h-full text-center">
                  <CardHeader>
                    <div className="mx-auto w-12 h-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mb-4">
                      <Book className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle>Backend Infrastructure</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Developed with Node.js and Express, with Flask microservices for ML model deployment and Firebase for lightweight data storage.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Research Areas Section */}
        <section className="py-16 md:py-24">
          <div className="container px-4 md:px-6">
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-bold tracking-tighter mb-4">Research Documentation</h2>
              <p className="max-w-[700px] mx-auto text-gray-600 dark:text-gray-300">
                Comprehensive analysis and findings from our year-long project.
              </p>
            </motion.div>

            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {researchTopics.map((topic, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="h-full">
                    <CardHeader className="flex flex-row items-start gap-4">
                      <div className="text-3xl font-bold text-primary opacity-50">
                        {topic.count}
                      </div>
                      <div>
                        <CardTitle>{topic.title}</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-2">
                      <p className="text-sm text-muted-foreground">
                        {topic.description}
                      </p>
                    </CardContent>
                    <CardFooter>
                      <Button variant="ghost" className="w-full">
                        View Documentation
                      </Button>
                    </CardFooter>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Team Section */}
        <section className="py-16 md:py-24 bg-primary/5">
          <div className="container px-4 md:px-6">
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-bold tracking-tighter mb-4">Project Team</h2>
              <p className="max-w-[700px] mx-auto text-gray-600 dark:text-gray-300">
                Interdisciplinary collaboration between computer science, psychology, and design students.
              </p>
            </motion.div>

            <motion.div
              className="flex flex-col items-center justify-center"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              <motion.div variants={itemVariants} className="text-center mb-6">
                <div className="flex justify-center mb-4">
                  <Users className="h-16 w-16 text-primary opacity-70" />
                </div>
                <h3 className="text-xl font-semibold">Supervised by Dr. Jane Smith</h3>
                <p className="text-sm text-muted-foreground mt-2">Associate Professor of Computer Science</p>
              </motion.div>
              
              <motion.div variants={itemVariants} className="max-w-2xl text-center">
                <p className="text-gray-600 dark:text-gray-300 italic">
                  "This project represents a significant contribution to understanding how AI can be ethically and effectively deployed in mental health contexts. The students have demonstrated exceptional technical skill while maintaining a focus on human-centered design."
                </p>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Academic FAQ Section */}
        <section className="py-16 md:py-24">
          <div className="container px-4 md:px-6">
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-bold tracking-tighter mb-4">Project FAQ</h2>
              <p className="max-w-[700px] mx-auto text-gray-600 dark:text-gray-300">
                Common questions about our research methodology and findings.
              </p>
            </motion.div>

            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="max-w-2xl mx-auto"
            >
              <Accordion type="single" collapsible className="space-y-4">
                <motion.div variants={itemVariants}>
                  <AccordionItem value="item-1">
                    <AccordionTrigger>What was the research methodology?</AccordionTrigger>
                    <AccordionContent>
                      We employed a mixed-methods approach combining qualitative interviews with 25 participants, 
                      quantitative data collection through our prototype, and comparative analysis with existing 
                      literature. All research protocols were approved by the university ethics committee.
                    </AccordionContent>
                  </AccordionItem>
                </motion.div>

                <motion.div variants={itemVariants}>
                  <AccordionItem value="item-2">
                    <AccordionTrigger>How accurate is the emotion detection?</AccordionTrigger>
                    <AccordionContent>
                      Our current model achieves 78% accuracy across seven emotional states using multimodal inputs 
                      (text, voice tone, and limited facial expression analysis). While promising for a student project, 
                      we've documented several limitations and potential improvements in our findings.
                    </AccordionContent>
                  </AccordionItem>
                </motion.div>

                <motion.div variants={itemVariants}>
                  <AccordionItem value="item-3">
                    <AccordionTrigger>Is this project open source?</AccordionTrigger>
                    <AccordionContent>
                      Yes, all code and documentation are available on GitHub under an MIT license. We encourage 
                      other students and researchers to build upon our work, with proper citation. The repository 
                      includes detailed setup instructions and API documentation.
                    </AccordionContent>
                  </AccordionItem>
                </motion.div>
              </Accordion>
            </motion.div>
          </div>
        </section>

        {/* Call to Action Section */}
        <motion.section
          className="bg-primary/5 py-16 md:py-24"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <h2 className="text-3xl font-bold tracking-tighter">Interested in Contributing?</h2>
              <p className="max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400">
                This project is seeking collaboration with researchers and students interested in AI ethics, 
                emotional wellbeing, and human-computer interaction.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mt-6">
                <Button size="lg">Download Paper</Button>
                <Button size="lg" variant="outline">
                  View GitHub Repository
                </Button>
              </div>
            </div>
          </div>
        </motion.section>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  )
}