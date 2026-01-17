
import {BrowserRouter as Router, Routes, Route, } from "react-router-dom";
// import routes from "./routes";
import Logs from "./pages/Logs";
import AddEmployee from "./pages/AddEmployee";
import LayoutMain from "./pages/LayoutMain";
import Employees from "./pages/Employees";
import LoginPage from "./pages/LogInPage";
import ProtectedRoute from "./components/ProtectedRoute";


function App() {
  return (



      <Router>
        <Routes>
            {/* <Route index element={<LayoutMain><Dashboard /></LayoutMain>} /> */}
            <Route path="/" element={<LoginPage />} />
            <Route path="logs" element={<ProtectedRoute><LayoutMain><Logs /></LayoutMain></ProtectedRoute>} />
            <Route path="add-employee" element={<ProtectedRoute><LayoutMain><AddEmployee /></LayoutMain></ProtectedRoute>} />
            <Route path="employees" element={<ProtectedRoute><LayoutMain><Employees /></LayoutMain></ProtectedRoute>} />
        </Routes>
      </Router>


  );
}

export default App;
