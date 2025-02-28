import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

// Import your page components
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import SignUp from './pages/SignUp'
import StressDetection from './pages/StressDetection'

function App() {
	return (
		<Router>
			<Routes>
				{/* Default route (Home) goes to Dashboard */}
				<Route path="/" element={<Dashboard/>}/>

				{/* Login and Register routes */}
				<Route path="/login" element={<Login/>}/>
				<Route path="/signup" element={<SignUp/>}/>
				<Route path="/stress-detection" element={<StressDetection/>}/>
			</Routes>
		</Router>
	)
}

export default App;
