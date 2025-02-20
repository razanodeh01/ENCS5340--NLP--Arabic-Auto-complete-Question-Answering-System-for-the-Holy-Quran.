import React, { useState, useEffect, useRef } from "react";
import './SearchBar.css'; // Ensure your CSS file is correctly imported
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faClock, faTimes } from '@fortawesome/free-solid-svg-icons'; // Import the clock icon
import axios from 'axios'; // Import axios for making HTTP requests

function SearchBar({ placeholder, data }) {
    const [filteredData, setFilteredData] = useState([]);
    const [relatedQuestions, setrelatedQuestions] = useState(null);
    const [wordEntered, setWordEntered] = useState("");
    const [wordQuestionEntered, setQuestionEntered] = useState("");
    const [selectedAnswer, setSelectedAnswer] = useState("");
    const [searchHistory, setSearchHistory] = useState([]);
    const [isListVisible, setIsListVisible] = useState(false);
    const searchBarRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (searchBarRef.current && !searchBarRef.current.contains(event.target)) {
                setIsListVisible(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
            setrelatedQuestions(null); // Clear related questions when typing starts

        };
    }, []);

    const handleFilter = async (event) => {
        const searchWord = event.target.value;
        setWordEntered(searchWord);
        setSelectedAnswer(""); // Clear the selected answer when typing starts
        setrelatedQuestions(null); // Clear related questions when typing starts
        if (searchWord === "") {
            setFilteredData(searchHistory);
        } else {
            try {
                const response = await axios.get('http://127.0.0.1:5000/autocomplete', { params: { query: searchWord } });
                setFilteredData(response.data.map(q => ({ q, a: "" }))); // Since we only get questions, set answers to empty
            } catch (error) {
                console.error("Error fetching suggestions: ", error);
            }
        }
        setIsListVisible(true); // Ensure list is visible when typing
    };

    const handleClick = async (question) => {
        setWordEntered(question);
        setQuestionEntered(question);
        try {
            const response = await axios.get('http://127.0.0.1:5000/search', { params: { query: question } });
            setSelectedAnswer(response.data.answer);
        } catch (error) {
            console.error("Error fetching answer: ", error);
        }
        setFilteredData([]);
        setSearchHistory((prevHistory) => {
            const updatedHistory = [{ q: question, a: selectedAnswer }, ...prevHistory.filter((item) => item.q !== question)];
            return updatedHistory.slice(0, 10); // Keep only the latest 10 searches
        });
    };

    const handleSearch = async (event) => {
        event.preventDefault();
        try {
            const response = await axios.get('http://127.0.0.1:5000/search', { params: { query: wordEntered } });
            setFilteredData([]);
            setSelectedAnswer(response.data.answer);
            setQuestionEntered(response.data.best_match);
            setrelatedQuestions(response.data.matches.slice(1, 10));
        } catch (error) {
            console.error("Error performing search: ", error);
        }
    };


    const handleRemoveHistoryItem = (question) => {
        setSearchHistory((prevHistory) => prevHistory.filter(item => item.q !== question));
    };

    return (
        <div className="row d-flex justify-content-center">
            <div className="col-md-6" ref={searchBarRef}>
                <form className="form" onSubmit={(e) => e.preventDefault()}>
                    <button type="submit" className="search-button" onClick={handleSearch}>
                        <i className="fa fa-search"></i>
                    </button>

                    <input
                        type="text"
                        placeholder={placeholder}
                        className="form-control form-input"
                        value={wordEntered}
                        onChange={handleFilter}
                        onFocus={() => {
                            if (wordEntered === "") {
                                setFilteredData(searchHistory);
                                setIsListVisible(true);
                            }
                        }}

                    />

                    {wordEntered && (
                        <button type="button" className="clear-button" onClick={() => {
                            setWordEntered("");
                            setSelectedAnswer("");
                            setFilteredData(searchHistory);
                            setIsListVisible(true);
                            setrelatedQuestions(null); // Clear related questions when typing starts
                        }}>
                            <i className="fa fa-times"></i>
                        </button>
                    )}

                </form>
                {isListVisible && filteredData.length !== 0 && (
                    <div className="dataResult">
                        {filteredData.slice(0, 15).map((value, index) => (
                            <div className={`list border-bottom d-flex justify-content-between align-items-center ${searchHistory.some(item => item.q === value.q) ? 'history-item' : ''}`} key={index}>
                                <div onClick={() => handleClick(value.q)} className="d-flex flex-column ml-3" style={{ flexGrow: 1 }}>
                                    <span>
                                        {searchHistory.some(item => item.q === value.q) && (
                                            <FontAwesomeIcon icon={faClock} />
                                        )}
                                        {value.q}
                                    </span>
                                </div>
                                {searchHistory.some(item => item.q === value.q) && (
                                    <button className="remove-button" onClick={() => handleRemoveHistoryItem(value.q)}>
                                        <FontAwesomeIcon icon={faTimes} />
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
                {selectedAnswer && (
                    <div className="answer">
                        <h3>:السؤال</h3>
                        <p>{wordQuestionEntered}</p>
                        <h3>:الإجابة</h3>
                        <p>{selectedAnswer}</p>
                    </div>
                )}
                {relatedQuestions && (
                    <div className="related-questions">
                        <h3>:أسئلة ذات صلة</h3>
                        <ul>
                            {relatedQuestions.map((question, index) => (
                                <li key={index} className="question">
                                    {question.q}
                                    <p className="popular-answer">{question.a}</p>
                                </li>
                            ))}
                        </ul>

                    </div>
                )}

            </div>
        </div>
    );
}

export default SearchBar;
