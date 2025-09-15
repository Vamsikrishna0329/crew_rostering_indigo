
import axios from "axios";
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/v1",
});
export const generateRoster = (payload) => api.post("/rosters/generate", payload).then(r => r.data);
export const getRosterCalendar = (params) => api.get("/rosters/calendar", { params }).then(r => r.data);
export const getCrewGantt = (params) => api.get("/rosters/crew-gantt", { params }).then(r => r.data);
export const getConflicts = (params) => api.get("/rosters/conflicts", { params }).then(r => r.data);
export const getDisruptions = (params) => api.get("/rosters/disruptions", { params }).then(r => r.data);
export const getRuleClassification = () => api.get("/rosters/rules/classification").then(r => r.data);
export const rerosterDelay = (payload) => api.post("/reroster", payload).then(r => r.data);
export const aiSuggest = (flight_no) => api.post("/ai/reroster_suggest", { flight_no }).then(r => r.data);
export const aiAsk = (question) => api.post("/ai/ask", { question }).then(r => r.data);
