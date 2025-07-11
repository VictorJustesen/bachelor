import React, { useState } from 'react';
import './Start.css';

function Start({ onEnterFree }) {
  const [showLogin, setShowLogin] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    firstName: '',
    lastName: ''
  });
  const [user, setUser] = useState(null);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setShowLogin(false);
      } else {
        alert('Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          first_name: formData.firstName,
          last_name: formData.lastName
        }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setShowLogin(false);
      } else {
        alert('Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('Registration failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const handleSubmit = isLogin ? handleLogin : handleRegister;

  return (
    <div className="start-wrapper">
      <h1 className="start-title">Bolig beregner</h1>

      {!user ? (
        <>
          {!showLogin ? (
            <div className="start-actions">
              <button className="start-button" onClick={() => setShowLogin(true)}>
                Login / Register
              </button>
              <button className="start-button" onClick={onEnterFree}>
                Enter Free Mode
              </button>
            </div>
          ) : (
            <div className="auth-form">
              <div className="form-toggle">
                <button
                  className={isLogin ? 'active' : ''}
                  onClick={() => setIsLogin(true)}
                >
                  Login
                </button>
                <button
                  className={!isLogin ? 'active' : ''}
                  onClick={() => setIsLogin(false)}
                >
                  Register
                </button>
              </div>
              <form onSubmit={handleSubmit}>
                <input
                  type="text"
                  name="username"
                  placeholder="Username"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                />
                {!isLogin && (
                  <>
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
                      name="firstName"
                      placeholder="First Name"
                      value={formData.firstName}
                      onChange={handleInputChange}
                    />
                    <input
                      type="text"
                      name="lastName"
                      placeholder="Last Name"
                      value={formData.lastName}
                      onChange={handleInputChange}
                    />
                  </>
                )}
                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                />
                <button type="submit" className="start-button">
                  {isLogin ? 'Login' : 'Register'}
                </button>
              </form>
              <button className="start-button back-button" onClick={() => setShowLogin(false)}>
                Back
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="user-welcome">
          <p>Welcome back, {user.first_name || user.username}!</p>
          <div className="user-options">
            <button className="start-button" onClick={onEnterFree}>
              Start Calculating
            </button>
            <button className="start-button logout-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Start;