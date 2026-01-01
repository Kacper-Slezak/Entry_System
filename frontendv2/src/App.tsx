
import { HashRouter, Routes, Route, } from "react-router-dom";
// import routes from "./routes";
import Dashboard from "./pages/Dashboard";
import AddEmployee from "./pages/AddEmployee";
import LayoutMain from "./pages/_layout";
import Employees from "./pages/Employees";


function App() {
  return (

      <HashRouter>
        {/* main route component */}
        <Routes>

            <Route path="/" element={<LayoutMain><Dashboard /></LayoutMain>} />
            <Route path='/add-employee' element={<LayoutMain><AddEmployee /></LayoutMain>} />
            <Route path='/employees' element={<LayoutMain><Employees /></LayoutMain>} />
        </Routes>
     </HashRouter>

  );
}

export default App;