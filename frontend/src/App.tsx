
import {BrowserRouter as Router, Routes, Route, } from "react-router-dom";
// import routes from "./routes";
import Dashboard from "./pages/Dashboard";
import AddEmployee from "./pages/AddEmployee";
import LayoutMain from "./pages/LayoutMain";
import Employees from "./pages/Employees";
import Logs from "./pages/Logs";


function App() {
  return (



      <Router>
        <Routes>
            {/* <Route index element={<LayoutMain><Dashboard /></LayoutMain>} /> */}
            <Route path="/" element={<LayoutMain><Dashboard /></LayoutMain>} />
            <Route path="add-employee" element={<LayoutMain><AddEmployee /></LayoutMain>} />
            <Route path="employees" element={<LayoutMain><Employees /></LayoutMain>} />
            <Route path="logs" element={<LayoutMain><Logs /></LayoutMain>} />
        </Routes>
      </Router>


  );
}

export default App;
