import React, { useState, useEffect } from 'react';
import './LoginSignup.css';
import { useNavigate } from 'react-router-dom';

function LoginSignup({ onLogin, isLogin: initialIsLogin }) {
  const [isLogin, setIsLogin] = useState(initialIsLogin !== undefined ? initialIsLogin : true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    fullName: ''
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Update isLogin state when prop changes
  useEffect(() => {
    if (initialIsLogin !== undefined) {
      setIsLogin(initialIsLogin);
    }
  }, [initialIsLogin]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const url = isLogin ? 'http://localhost:8000/api/login/' : 'http://localhost:8000/api/signup/';
    const data = isLogin ? 
      { username: formData.username, password: formData.password } :
      {
        username: formData.username,
        password: formData.password,
        email: formData.email,
        fullName: formData.fullName
      };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (response.ok) {
        if (result.success) {
          // Pass the token from the result if available
          onLogin(result.token || 'dummy-token');
          navigate('/dashboard');
        } else {
          setError(result.message || 'An error occurred');
        }
      } else {
        setError(result.message || 'An error occurred');
      }
    } catch (err) {
      console.error('Error:', err);
      setError('An error occurred. Please try again.');
    }
  };

  const toggleLoginMode = () => {
    setIsLogin(!isLogin);
    setError('');
  };

  return (
    <div className="container">
      <div className="form-container">
        <div className={`form-box ${isLogin ? 'active' : 'inactive'}`}>
          <h2>Login</h2>
          {isLogin && (
            <form onSubmit={handleSubmit}>
              <input 
                type="text" 
                name="username"
                placeholder="Username"
                value={formData.username}
                onChange={handleInputChange}
                required
              />
              <input 
                type="password"
                name="password" 
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange}
                required
              />
              {error && <div className="error-message">{error}</div>}
              <button type="submit">Login</button>
            </form>
          )}
          {!isLogin && (
            <div className="switch-form">
              Already have an account? <a onClick={toggleLoginMode}>Log in here</a>
            </div>
          )}
        </div>
        <div className={`form-box ${!isLogin ? 'active' : 'inactive'}`}>
          <h2>Sign Up</h2>
          {!isLogin && (
            <form onSubmit={handleSubmit}>
              <input 
                type="text"
                name="fullName"
                placeholder="Full Name"
                value={formData.fullName}
                onChange={handleInputChange}
                required
              />
              <input 
                type="email"
                name="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleInputChange}
                required
              />
              <input 
                type="text"
                name="username"
                placeholder="Username"
                value={formData.username}
                onChange={handleInputChange}
                required
              />
              <input 
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange}
                required
              />
              {error && <div className="error-message">{error}</div>}
              <button type="submit">Sign Up</button>
            </form>
          )}
          {isLogin && (
            <div className="switch-form">
              Don't have an account? <a onClick={toggleLoginMode}>Sign up here</a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default LoginSignup;
