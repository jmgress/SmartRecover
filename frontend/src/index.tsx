import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Prevent transitions on initial page load
document.documentElement.classList.add('no-transition');

// Remove the no-transition class after initial render to enable smooth theme transitions
// Using requestAnimationFrame ensures this happens after the initial paint
requestAnimationFrame(() => {
  setTimeout(() => {
    document.documentElement.classList.remove('no-transition');
  }, 0);
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
