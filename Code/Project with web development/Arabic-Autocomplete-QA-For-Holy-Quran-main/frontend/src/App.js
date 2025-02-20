import React, { useState, useEffect } from "react";
import "./App.css";
import SearchBar from "./Component/SearchBar";
import axios from "axios";

function App() {
  const [activeIndex, setActiveIndex] = useState(null);  // State to track the active question
  const [popularQuestions, setPopularQuestions] = useState([]);

  useEffect(() => {
    // Fetch popular-questions from the Flask server
    const fetchQuestions = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/popular-questions');
        setPopularQuestions(response.data);
      } catch (error) {
        console.error("Error fetching popular questions: ", error);
      }
    };

    fetchQuestions();
  }, []);

  const toggleQuestion = index => {
    // Toggle active question to expand/collapse answers
    setActiveIndex(activeIndex === index ? null : index);
  };

  return (
    <div className="App">
      <SearchBar placeholder="ابحث هنا ..." />
      <h2>الأسئلة الشائعة</h2>
      <div className="popular-questions-container">
        <ul className="popular-questions">
          {popularQuestions.map((question, index) => (
            <li key={index} className="question">
              {question.q}
              <p className="popular-answer">{question.a}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}



export default App;
