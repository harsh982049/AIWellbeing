import { useState } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Link } from "react-router-dom"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { Calendar, ChevronLeft, ChevronRight, Edit, Camera, Music } from "lucide-react"

// Mock data for visualizations
const generateDailyData = () => {
  const data = []
  for (let i = 0; i < 24; i++) {
    data.push({
      hour: `${i}:00`,
      stressLevel: Math.floor(Math.random() * 70) + 10,
    })
  }
  return data
}

const generateWeeklyData = () => {
  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
  return days.map((day) => ({
    day,
    stressLevel: Math.floor(Math.random() * 70) + 10,
    anxious: Math.floor(Math.random() * 30),
    neutral: Math.floor(Math.random() * 40),
    happy: Math.floor(Math.random() * 30),
  }))
}

const generateMonthlyData = () => {
  const data = []
  for (let i = 1; i <= 30; i++) {
    data.push({
      date: `${i}`,
      stressLevel: Math.floor(Math.random() * 70) + 10,
    })
  }
  return data
}

const emotionData = [
  { name: "Happy", value: 30, color: "#4ade80" },
  { name: "Neutral", value: 40, color: "#facc15" },
  { name: "Anxious", value: 20, color: "#fb923c" },
  { name: "Stressed", value: 10, color: "#ef4444" },
]

const annotations = [
  { date: "Monday", note: "Had an important meeting" },
  { date: "Thursday", note: "Deadline for project submission" },
  { date: "Saturday", note: "Relaxed at home" },
]

const StressVisualizationPage = () => {
  const [timeRange, setTimeRange] = useState("weekly")
  const [currentDate, setCurrentDate] = useState(new Date())
  const [annotationText, setAnnotationText] = useState("")
  const [selectedDay, setSelectedDay] = useState(null)

  // Get data based on selected time range
  const getData = () => {
    switch (timeRange) {
      case "daily":
        return generateDailyData()
      case "monthly":
        return generateMonthlyData()
      case "weekly":
      default:
        return generateWeeklyData()
    }
  }

  // Format date for display
  const formatDate = (date) => {
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    })
  }

  // Navigate to previous period
  const goToPrevious = () => {
    const newDate = new Date(currentDate)
    if (timeRange === "daily") {
      newDate.setDate(newDate.getDate() - 1)
    } else if (timeRange === "weekly") {
      newDate.setDate(newDate.getDate() - 7)
    } else {
      newDate.setMonth(newDate.getMonth() - 1)
    }
    setCurrentDate(newDate)
  }

  // Navigate to next period
  const goToNext = () => {
    const newDate = new Date(currentDate)
    if (timeRange === "daily") {
      newDate.setDate(newDate.getDate() + 1)
    } else if (timeRange === "weekly") {
      newDate.setDate(newDate.getDate() + 7)
    } else {
      newDate.setMonth(newDate.getMonth() + 1)
    }
    setCurrentDate(newDate)
  }

  // Handle adding a new annotation
  const handleAddAnnotation = () => {
    // In a real app, you would save this to your data store
    console.log(`Added annotation for ${selectedDay}: ${annotationText}`)
    setAnnotationText("")
  }

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
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

  return (
    <motion.div className="container mx-auto px-4 py-8" variants={containerVariants} initial="hidden" animate="visible">
      <motion.div variants={itemVariants} className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Stress Visualization</h1>
        <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          Track your stress levels and emotional patterns over time to identify triggers and monitor your progress.
        </p>
      </motion.div>

      {/* Time Range Controls */}
      <motion.div variants={itemVariants} className="mb-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-2">
                <Button variant="outline" size="icon" onClick={goToPrevious}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <div className="flex items-center">
                  <Calendar className="mr-2 h-4 w-4" />
                  <span>{formatDate(currentDate)}</span>
                </div>
                <Button variant="outline" size="icon" onClick={goToNext}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select time range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily View</SelectItem>
                  <SelectItem value="weekly">Weekly View</SelectItem>
                  <SelectItem value="monthly">Monthly View</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Stress Level Trends</CardTitle>
              <CardDescription>
                {timeRange === "daily"
                  ? "Hourly stress levels for the selected day"
                  : timeRange === "weekly"
                    ? "Daily stress levels for the selected week"
                    : "Daily stress levels for the selected month"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  {timeRange === "weekly" ? (
                    <BarChart data={getData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="stressLevel" fill="#8884d8" name="Stress Level" />
                    </BarChart>
                  ) : (
                    <LineChart data={getData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey={timeRange === "daily" ? "hour" : "date"} />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="stressLevel"
                        stroke="#8884d8"
                        activeDot={{ r: 8 }}
                        name="Stress Level"
                      />
                    </LineChart>
                  )}
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Emotion Distribution */}
        <motion.div variants={itemVariants}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Emotion Distribution</CardTitle>
              <CardDescription>Breakdown of your emotional states</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={emotionData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {emotionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Annotations */}
      <motion.div variants={itemVariants} className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Edit className="mr-2 h-5 w-5" /> Annotations
            </CardTitle>
            <CardDescription>Add notes about specific days to track triggers and events</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium mb-2">Existing Annotations</h3>
                {annotations.length > 0 ? (
                  <div className="space-y-2">
                    {annotations.map((annotation, index) => (
                      <div key={index} className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                        <div className="font-medium">{annotation.date}</div>
                        <div className="text-gray-600 dark:text-gray-300">{annotation.note}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">No annotations yet</p>
                )}
              </div>
              <div>
                <h3 className="font-medium mb-2">Add New Annotation</h3>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="w-full">
                      Add Annotation
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Annotation</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="day">Select Day</Label>
                        <Select onValueChange={setSelectedDay}>
                          <SelectTrigger id="day">
                            <SelectValue placeholder="Select a day" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Monday">Monday</SelectItem>
                            <SelectItem value="Tuesday">Tuesday</SelectItem>
                            <SelectItem value="Wednesday">Wednesday</SelectItem>
                            <SelectItem value="Thursday">Thursday</SelectItem>
                            <SelectItem value="Friday">Friday</SelectItem>
                            <SelectItem value="Saturday">Saturday</SelectItem>
                            <SelectItem value="Sunday">Sunday</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="annotation">Annotation</Label>
                        <Textarea
                          id="annotation"
                          placeholder="What happened on this day?"
                          value={annotationText}
                          onChange={(e) => setAnnotationText(e.target.value)}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button variant="outline">Cancel</Button>
                      </DialogClose>
                      <Button onClick={handleAddAnnotation}>Save Annotation</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Call to Action */}
      <motion.div variants={itemVariants} className="mt-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/stress-detection">
                <Button variant="outline" className="w-full sm:w-auto">
                  <Camera className="mr-2 h-4 w-4" /> Return to Stress Detection
                </Button>
              </Link>
              <Link to="/relaxation-therapy">
                <Button className="w-full sm:w-auto">
                  <Music className="mr-2 h-4 w-4" /> Explore Relaxation Techniques
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

export default StressVisualizationPage

