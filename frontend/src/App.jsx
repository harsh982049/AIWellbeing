import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

// Import your page components
import Dashboard from './pages/Dashboard'
// import Login from './pages/Login'
// import Register from './pages/Register'

function App() {
	return (
		<Router>
			<Routes>
				{/* Default route (Home) goes to Dashboard */}
				<Route path="/" element={<Dashboard />} />

				{/* Login and Register routes */}
				{/* <Route path="/login" element={<Login />} />
				<Route path="/register" element={<Register />} /> */}
			</Routes>
		</Router>
	)
}

export default App;
