import React, { useState, useEffect } from 'react';

import Header from './components/Header/Header';
import './App.css';
interface Product {
  id: string;
  title: string;
  price: number; // "+" to convert string to number
}

function App() {
  const [loadedProducts, setLoadedProducts] = useState<Product[]>();
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
  }, []);


  return (
    <React.Fragment>
      <Header />
      <main className="container">
        {`${process.env.REACT_APP_HOST}:${process.env.PORT}`}
      </main>
    </React.Fragment>
  );
}

export default App;