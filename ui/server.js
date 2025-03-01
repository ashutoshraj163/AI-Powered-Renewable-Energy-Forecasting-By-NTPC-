const express = require("express");
const fs = require("fs");
const cors = require("cors");

const app = express();
app.use(express.json());
app.use(cors());

const USERS_FILE = "users.json";

// Function to read users
const readUsers = () => {
    return JSON.parse(fs.readFileSync(USERS_FILE, "utf8"));
};

// Function to write users
const writeUsers = (users) => {
    fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
};

// Register Route
app.post("/register", (req, res) => {
    const { username, password } = req.body;
    let users = readUsers();

    // Check if user already exists
    if (users.find(user => user.username === username)) {
        return res.json({ success: false });
    }

    users.push({ username, password });
    writeUsers(users);

    res.json({ success: true });
});

// Login Route
app.post("/login", (req, res) => {
    const { username, password } = req.body;
    const users = readUsers();

    const user = users.find(user => user.username === username && user.password === password);

    if (user) {
        res.json({ success: true });
    } else {
        res.json({ success: false });
    }
});

// Start Server
app.listen(3003, () => console.log("Server running on http://localhost:3000"));
