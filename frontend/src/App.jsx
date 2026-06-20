import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Analyzer from "./pages/Analyzer.jsx";
import Campaigns from "./pages/Campaigns.jsx";
import CampaignDetail from "./pages/CampaignDetail.jsx";
import Users from "./pages/Users.jsx";
import UserDetail from "./pages/UserDetail.jsx";
import Compliance from "./pages/Compliance.jsx";

const NAV = [
  { to: "/", label: "Dashboard", icon: "▦", end: true },
  { to: "/analyzer", label: "Email Analyzer", icon: "🔬" },
  { to: "/campaigns", label: "Campaigns", icon: "🎯" },
  { to: "/users", label: "Users & Risk", icon: "👥" },
  { to: "/compliance", label: "Compliance", icon: "✓" },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="logo">🛡️</div>
        <div>
          <div className="title">PhishGuard</div>
          <div className="sub">Awareness Training Platform</div>
        </div>
      </div>
      <nav className="nav">
        {NAV.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end}
            className={({ isActive }) => (isActive ? "active" : "")}>
            <span className="ico">{n.icon}</span>
            {n.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-foot">
        <div className="sim-pill">● Simulation mode — no real emails sent</div>
        <div style={{ marginTop: 10 }}>Computer Security · Final Project</div>
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <div className="app">
      <Sidebar />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyzer" element={<Analyzer />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/campaigns/:id" element={<CampaignDetail />} />
          <Route path="/users" element={<Users />} />
          <Route path="/users/:id" element={<UserDetail />} />
          <Route path="/compliance" element={<Compliance />} />
        </Routes>
      </main>
    </div>
  );
}
