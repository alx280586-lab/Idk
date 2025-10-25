import React from 'react';

const Header = () => (
  <header className="app-header">
    <div>
      <h1>AutoClipper AI</h1>
      <p>Fully autonomous short-form content engine for your long-form videos.</p>
    </div>
    <div className="header-actions">
      <span className="badge">Beta</span>
      <a className="link" href="https://openai.com" target="_blank" rel="noreferrer">
        Docs
      </a>
    </div>
  </header>
);

export default Header;
