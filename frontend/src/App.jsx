import { useEffect, useState } from "react";
import API from "./services/api";

function App() {

  const [data, setData] = useState([]);

  useEffect(() => {
    API.get("/business-data")
      .then((response) => {
        console.log(response.data);
        setData(response.data);
      })
      .catch((error) => console.error(error));
  }, []);

  return (
    <div>
      <h1>Business Decision Intelligence System</h1>

      <table border="1">
        <thead>
          <tr>
            <th>Month</th>
            <th>Revenue</th>
            <th>Expenses</th>
            <th>Marketing</th>
            <th>Customer Growth</th>
          </tr>
        </thead>

        <tbody>
          {data.map((row) => (
            <tr key={row.id}>
              <td>{row.month}</td>
              <td>{row.revenue}</td>
              <td>{row.expenses}</td>
              <td>{row.marketing_spend}</td>
              <td>{row.customer_growth}</td>
            </tr>
          ))}
        </tbody>

      </table>
    </div>
  );
}

export default App;