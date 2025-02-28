// File: src/pages/StressDetection.jsx

import { useState, useEffect } from "react"
/* eslint-disable-next-line no-unused-vars */
import { motion } from "framer-motion"
import Webcam from "react-webcam"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle, Camera, Music } from "lucide-react"
import Navbar from "@/components/Navbar"
import Footer from "@/components/Footer"

function StressDetection() {
    const [isWebcamActive, setIsWebcamActive] = useState(false)
    const [detectedEmotion, setDetectedEmotion] = useState(null)
    const [stressLevel, setStressLevel] = useState(null)

    // Animation variants
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.3 },
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

    // Simulated stress detection (replace with actual backend integration)
    const detectStress = () => {
        const emotions = ["Calm", "Happy", "Anxious", "Stressed", "Neutral"]
        const levels = ["Low", "Medium", "High"]

        setInterval(() => {
            setDetectedEmotion(emotions[Math.floor(Math.random() * emotions.length)])
            setStressLevel(levels[Math.floor(Math.random() * levels.length)])
            }, 3000) // Update every 3 seconds for demo purposes
    }

    const activateWebcam = () => {
        setIsWebcamActive(true)
        detectStress() // Start simulated stress detection
    }

    const getSuggestion = () => {
        switch (stressLevel) {
            case "Low":
                return "Great job managing your stress! Keep up your current routines."
            case "Medium":
                return "Consider taking a short break or doing some deep breathing exercises."
            case "High":
                return "It's important to address your stress. Try our guided relaxation techniques or speak with a professional."
            default:
                return "Waiting for stress level detection..."
        }
    }

    useEffect(() => {
        return () => {
        // No manual cleanup needed for react-webcam
        }
    }, [])

    return (
        <div className="flex min-h-screen flex-col">
            <Navbar />
            <motion.div
                className="container mx-auto px-4 py-8 max-w-4xl"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                <motion.header variants={itemVariants} className="text-center mb-8">
                <h1 className="text-3xl font-bold mb-4">AI Stress Detection</h1>
                <p className="text-lg text-gray-600 dark:text-gray-300">
                    Our advanced AI system uses live webcam video to detect your current emotion and stress level in real-time.
                    This data helps us provide personalized suggestions to improve your emotional wellbeing and manage stress effectively.
                </p>
                </motion.header>

                {!isWebcamActive ? (
                <motion.div variants={itemVariants} className="flex justify-center">
                    <Card>
                    <CardHeader>
                        <CardTitle>Live Webcam Feed</CardTitle>
                    </CardHeader>
                    <CardContent className="flex justify-center">
                        <Button size="lg" onClick={activateWebcam} className="bg-blue-600 hover:bg-blue-700 text-white">
                        <Camera className="mr-2 h-5 w-5" /> Activate Webcam
                        </Button>
                    </CardContent>
                    </Card>
                </motion.div>
                ) : (
                <div className="flex flex-col md:flex-row gap-6">
                    {/* Left Column: Webcam Feed */}
                    <motion.div className="w-full md:w-1/2" variants={itemVariants}>
                    <Card>
                        <CardHeader>
                        <CardTitle>Live Webcam Feed</CardTitle>
                        </CardHeader>
                        <CardContent className="flex justify-center">
                        <div className="w-full max-w-md mx-auto">
                            <Card className="border rounded-lg overflow-hidden">
                            <Webcam
                                audio={false}
                                screenshotFormat="image/jpeg"
                                className="w-full h-auto"
                            />
                            </Card>
                        </div>
                        </CardContent>
                    </Card>
                    </motion.div>

                    {/* Right Column: Results */}
                    <motion.div className="w-full md:w-1/2 flex flex-col gap-6" variants={itemVariants}>
                    <Card>
                        <CardHeader>
                        <CardTitle>Detected Emotion</CardTitle>
                        </CardHeader>
                        <CardContent>
                        <p className="text-2xl font-semibold text-center">
                            {detectedEmotion || "Analyzing..."}
                        </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                        <CardTitle>Stress Level</CardTitle>
                        </CardHeader>
                        <CardContent>
                        <p className="text-2xl font-semibold text-center">
                            {stressLevel || "Analyzing..."}
                        </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                        <CardTitle>Personalized Suggestion</CardTitle>
                        </CardHeader>
                        <CardContent>
                        <p className="text-lg">{getSuggestion()}</p>
                        {stressLevel === "High" && (
                            <motion.div
                            className="mt-4 flex justify-center"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                            >
                            <Button size="lg" className="bg-red-600 hover:bg-red-700 text-white mr-4">
                                <AlertCircle className="mr-2 h-5 w-5" /> Panic SOS
                            </Button>
                            <Button size="lg" className="bg-green-600 hover:bg-green-700 text-white">
                                <Music className="mr-2 h-5 w-5" /> Music Therapy
                            </Button>
                            </motion.div>
                        )}
                        </CardContent>
                    </Card>
                    </motion.div>
                </div>
                )}
            </motion.div>
            <Footer/>
        </div>
    )
}

export default StressDetection
