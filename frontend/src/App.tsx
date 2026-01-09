
import {BrowserRouter as Router, Routes, Route, } from "react-router-dom";
// import routes from "./routes";
import Logs from "./pages/Logs";
import AddEmployee from "./pages/AddEmployee";
import LayoutMain from "./pages/LayoutMain";
import Employees from "./pages/Employees";


function App() {
  return (
      <Router>
        <Routes>
            {/* <Route index element={<LayoutMain><Dashboard /></LayoutMain>} /> */}
            <Route path="/" element={<LayoutMain><Logs /></LayoutMain>} />
            <Route path="add-employee" element={<LayoutMain><AddEmployee /></LayoutMain>} />
            <Route path="employees" element={<LayoutMain><Employees /></LayoutMain>} />
        </Routes>
      </Router>


  );
}

export default App;
