// firebase-config.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-app.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyB26wWhMvOOIYMQkw-3aIFsxtz2SSI36FQ",
  authDomain: "cold-storage-iot.firebaseapp.com",
  databaseURL: "https://cold-storage-iot-default-rtdb.firebaseio.com/",
  projectId: "cold-storage-iot",
  storageBucket: "cold-storage-iot.firebasestorage.app",
  messagingSenderId: "635229451246",
  appId: "1:635229451246:web:118f5f92fa6def217114ff",
  measurementId: "G-NP8EZS073H"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const db = getDatabase(app);

