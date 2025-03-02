import React from 'react';
import {BrowserRouter as Router, Routes, Route} from 'react-router-dom';
// import './App.css'

// Import your page components
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import StressDetection from './pages/StressDetection';
import PanicSOSChatbot from './pages/PanicSOSChatbot';

function App() {
	return (
		<Router>
			<Routes>
				<Route path="/" element={<Dashboard/>}/>

				{/* Login and Register routes */}
				<Route path="/login" element={<Login/>}/>
				<Route path="/signup" element={<SignUp/>}/>
				<Route path="/stress-detection" element={<StressDetection/>}/>
				<Route path="/panic-chatbot" element={<PanicSOSChatbot/>}/>
			</Routes>
		</Router>
	)
}

export default App;
