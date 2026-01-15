
import {BrowserRouter as Router,Routes, Route, Navigate, } from "react-router-dom";
// import routes from "./routes";
import Logs from "./pages/Logs";
import AddEmployee from "./pages/AddEmployee";
import LayoutMain from "./pages/LayoutMain";
import EmployeesPage from "./pages/Employees";
import EditEmployee from "./pages/EditEmployee";


function App() {
  return (
      <Router>
        <Routes>
            <Route path="/" element={<LayoutMain><Logs /></LayoutMain>} />
            <Route path="add-employee" element={<LayoutMain><AddEmployee /></LayoutMain>} />
            <Route path="employees" element={<LayoutMain><EmployeesPage /></LayoutMain>} />
            <Route path="edit-employee/:uuid" element={<LayoutMain><EditEmployee /></LayoutMain>} />
            <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>


  );
}

export default App;
