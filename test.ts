// vulnerable.ts

import express from 'express';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import axios from 'axios';

const app = express();
app.use(express.json());

// 🚨 Hardcoded credentials
const DB_USER = 'admin';
const DB_PASS = 'SuperSecret123';

// 🚨 Insecure Deserialization
app.post('/deserialize', (req, res) => {
  try {
    const data = JSON.parse(req.body.payload); // Unsanitized JSON input
    res.send(`Deserialized: ${data}`);
  } catch (err) {
    res.status(500).send('Error deserializing');
  }
});

// 🚨 Eval injection
app.post('/eval', (req, res) => {
  const code = req.body.code;
  try {
    const result = eval(code); // Dangerous: user-supplied code
    res.send(`Result: ${result}`);
  } catch {
    res.status(400).send('Invalid code');
  }
});

// 🚨 Path traversal
app.get('/read-file', (req, res) => {
  const filename = req.query.name as string;
  const filePath = path.join(__dirname, 'files', filename); // No sanitization
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) return res.status(500).send('Error reading file');
    res.send(data);
  });
});

// 🚨 Command injection
app.post('/ping', (req, res) => {
  const host = req.body.host;
  exec(`ping -c 2 ${host}`, (error, stdout) => {
    if (error) return res.status(500).send('Ping failed');
    res.send(stdout);
  });
});

// 🚨 Prototype pollution
app.post('/pollute', (req, res) => {
  const obj = {};
  Object.assign(obj, req.body); // Can modify Object.prototype
  res.send(obj);
});

// 🚨 SSRF
app.post('/fetch-url', async (req, res) => {
  const url = req.body.url;
  try {
    const response = await axios.get(url); // No whitelist
    res.send(response.data);
  } catch {
    res.status(400).send('Invalid request');
  }
});

// 🚨 Regular Expression Denial of Service (ReDoS)
app.post('/search', (req, res) => {
  const query = req.body.query;
  const regex = new RegExp(query); // May cause catastrophic backtracking
  const result = 'a'.repeat(10000).match(regex);
  res.send(result ? 'Match' : 'No Match');
});

app.listen(3000, () => {
  console.log('Vulnerable app running on port 3000');
});
