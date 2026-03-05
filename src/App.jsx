import React, { useState} from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useParams } from "react-router-dom";
import './App.css';

function App(){
  const [count, setCount]= useState(0);
  const handleClick = ()=>{
    setCount(count+1);
  };
  return(
    <div className='app'>
      <h1>Котики мяу мяу</h1>
      <p> собачки гав гав</p>
      <button onClick={handleClick}>
        нажми {count}
      </button>
      {count>0 &&(
        <p>ты нажмакал {count} раз</p>
      )}
    </div>
  );
}
export default App;