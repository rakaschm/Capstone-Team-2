import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import UserInterestComponent from './components/user_interest_component'
import PropertyTable from './components/rental_list_component'

function App() {
  const [count, setCount] = useState(0)

  // Get userId from query string
  const params = new URLSearchParams(window.location.search)
  const userId = params.get('userId') || '4' // fallback to '4' if not present

  // State to control PropertyTable visibility
  const [showProperties, setShowProperties] = useState(false)

  // Handler for recommendations button click
  const handleRecommendationsClick = () => {
    setShowProperties(true)
  }

  return (
    <>
      {/* <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div> */}
      {/* <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div> */}

      <UserInterestComponent userId={userId} onRecommendationsClick={handleRecommendationsClick} />
      {showProperties && (
        <PropertyTable apiUrl={`http://localhost:8000/users/${userId}/properties`} />
      )}
    </>
  )
}

export default App
