// A (very) simple simulated database for users
const fakeUsersDb = {
  "1": {
    email: "user@example.com",
    name: "Test User"
  }
};

const loginUser = (req, res) => {
  const { email, password } = req.body;

  // In a real application, you would:
  // 1. Find the user in a real database by email.
  // 2. Use a library like 'bcrypt' to compare the hashed password.
  if (email === 'user@example.com' && password === 'fakepassword') {
    res.json({
      message: "Login successful!",
      token: "fake-jwt-token", // You would generate a real JWT here
      user: {
        id: 1,
        email: "user@example.com",
        name: "Test User"
      }
    });
  } else {
    res.status(401).json({ error: "Incorrect email or password" });
  }
};

const getUserInfo = (req, res) => {
    const { userId } = req.params;
    const user = fakeUsersDb[userId];

    if (user) {
        // In a real app, you would verify a JWT token here before returning data
        res.json(user);
    } else {
        res.status(404).json({ error: "User not found" });
    }
};

module.exports = { loginUser, getUserInfo };