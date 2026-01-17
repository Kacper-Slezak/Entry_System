
import {BrowserRouter as Router,Routes, Route, Navigate, } from "react-router-dom";
// import routes from "./routes";
import Logs from "./pages/Logs";
import AddEmployee from "./pages/AddEmployee";
import LayoutMain from "./pages/LayoutMain";
import LoginPage from "./pages/LogInPage";
import ProtectedRoute from "./components/ProtectedRoute";
import EmployeesPage from "./pages/Employees";
import EditEmployee from "./pages/EditEmployee";


function App() {
  return (
      <Router>
        <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="logs" element={<ProtectedRoute><LayoutMain><Logs /></LayoutMain></ProtectedRoute>} />
            <Route path="add-employee" element={<ProtectedRoute><LayoutMain><AddEmployee /></LayoutMain></ProtectedRoute>} />
            <Route path="employees" element={<ProtectedRoute><LayoutMain><EmployeesPage /></LayoutMain></ProtectedRoute>} />
            <Route path="edit-employee/:uuid" element={<ProtectedRoute><LayoutMain><EditEmployee /></LayoutMain></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>


  );
}

export default App;
