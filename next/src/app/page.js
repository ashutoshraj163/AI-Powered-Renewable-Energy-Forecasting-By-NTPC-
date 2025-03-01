'use client';

import { Wind, Sun, Activity, ArrowRight, Zap, BarChart3 } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useState, useEffect } from 'react';

const generateWaveData = (offset) => {
  const getDemandValue = (hour) => {
    if (hour <= 3) return 15000 - (hour * 700);
    if (hour <= 6) return 13000 - ((hour - 3) * 600);
    if (hour <= 9) return 11000 + Math.sin(hour) * 100;
    if (hour <= 12) return 11000 + ((hour - 9) * 400);
    if (hour <= 15) return 12200 - ((hour - 12) * 200);
    if (hour <= 18) return 11500 + Math.sin(hour) * 200;
    if (hour <= 21) return 11500 + ((hour - 18) * 1000);
    return 14500 + Math.sin(hour) * 100;
  };

  return Array(24).fill().map((_, i) => ({
    time: i,
    windValue: 600 + Math.sin((i + offset) / 8) * 100 + i * 10,
    windForecast: 590 + Math.sin((i + offset) / 8) * 100 + i * 10,
    solarValue: i >= 6 && i <= 18
      ? Math.sin((i - 6) * Math.PI / 12) * 300
      : 0,
    solarForecast: i >= 6 && i <= 18
      ? Math.sin((i - 6) * Math.PI / 12) * 290
      : 0,
    demandValue: getDemandValue(i),
    demandForecast: getDemandValue(i) + (Math.random() * 50 - 25),
  }));
};

export default function EnergyDashboard() {
  const [data, setData] = useState(generateWaveData(0));
  const [offset, setOffset] = useState(0);
  const [activeChart, setActiveChart] = useState('wind');

  useEffect(() => {
    const timer = setInterval(() => {
      setOffset(prev => prev + 1);
      setData(generateWaveData(offset));
    }, 100);
    return () => clearInterval(timer);
  }, [offset]);

  const handleDemoClick = () => {
    window.open('http://localhost:8501/');
  };
  const metrics = [
    {
      icon: Wind,
      label: "Wind Prediction",
      accuracy: "82%",
      color: "text-blue-400",
      key: 'wind'
    },
    {
      icon: Sun,
      label: "Solar Prediction",
      accuracy: "97%",
      color: "text-yellow-400",
      key: 'solar'
    },
    {
      icon: Zap,
      label: "Demand Prediction",
      accuracy: "94%",
      color: "text-purple-400",
      key: 'demand'
    },
    {
      icon: BarChart3,
      label: "Grid Optimization",
      accuracy: "Grid",
      color: "text-emerald-400",
      key: 'grid'
    }
  ];

  const [currentSlide, setCurrentSlide] = useState(0);

  const handlePrevClick = () => {
    setCurrentSlide((prev) => (prev === 0 ? 2 : prev - 1));
  };

  const handleNextClick = () => {
    setCurrentSlide((prev) => (prev === 2 ? 0 : prev + 1));
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col">
      <div className="container mx-auto px-4 py-12 flex-grow">
        <div className="flex justify-center mb-8">
          <div className="bg-slate-800/50 rounded-full px-6 py-2 flex flex-wrap justify-center gap-8">
            {metrics.map(({ icon: Icon, label, accuracy, color }) => (
              <span key={label} className="flex items-center">
                <Icon className={`w-4 h-4 mr-2 ${color}`} />
                <span className="text-sm">{accuracy}</span>
              </span>
            ))}
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h1 className="text-6xl font-bold">
              <span className="bg-gradient-to-r from-blue-400 via-emerald-400 to-yellow-400 bg-clip-text text-transparent">
                Predict Tomorrow's Energy Today
              </span>
            </h1>

            <p className="text-xl text-slate-300">
              EcoVolt delivers comprehensive energy forecasting powered by advanced AI. Transform your grid operations with real-time predictions for wind, solar, and demand patterns.
            </p>

            <div className="flex space-x-4">
              <button
                onClick={handleDemoClick}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 rounded-lg flex items-center transition-all"
              >
                Start Forecasting
                <ArrowRight className="ml-2 w-4 h-4" />
              </button>
              <button
                onClick={handleDemoClick}
                className="px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg transition-all"
              >
                View Demo
              </button>
            </div>
          </div>

          <div className="bg-slate-800/50 rounded-2xl p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="text-sm text-slate-400">Live Prediction Demo</div>
              <div className="flex gap-2">
                {['wind', 'solar', 'demand'].map(type => (
                  <button
                    key={type}
                    onClick={() => setActiveChart(type)}
                    className={`px-3 py-1 rounded-lg text-sm ${activeChart === type ? 'bg-blue-500' : 'bg-slate-700'
                      }`}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="time"
                    stroke="#9CA3AF"
                    axisLine={false}
                    tickLine={false}
                    tick={false}
                  />
                  <YAxis
                    stroke="#9CA3AF"
                    axisLine={false}
                    tickLine={false}
                    tick={false}
                    domain={
                      activeChart === 'demand'
                        ? [10000, 15500]
                        : activeChart === 'wind'
                          ? [0, 1000]
                          : [0, 500]
                    }
                  />
                  <Line
                    type="monotone"
                    dataKey={`${activeChart}Value`}
                    stroke={
                      activeChart === 'wind' ? '#60a5fa' :
                        activeChart === 'solar' ? '#fbbf24' :
                          '#ef4444'
                    }
                    strokeWidth={3}
                    dot={false}
                    isAnimationActive={true}
                    animationDuration={300}
                  />
                  <Line
                    type="monotone"
                    dataKey={`${activeChart}Forecast`}
                    stroke={
                      activeChart === 'wind' ? '#60a5fa' :
                        activeChart === 'solar' ? '#fbbf24' :
                          '#ef4444'
                    }
                    strokeWidth={2}
                    dot={false}
                    strokeDasharray="5 5"
                    isAnimationActive={true}
                    animationDuration={300}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-4 gap-8 mt-24">
          {metrics.map(({ icon: Icon, label, color, key }) => (
            <div key={key} className="bg-slate-800/50 p-6 rounded-xl">
              <Icon className={`w-8 h-8 ${color} mb-4`} />
              <h3 className="text-xl font-bold mb-2">{label}</h3>
              <p className="text-slate-400">
                {key === 'wind' && "Advanced wind power forecasting based on weather predictions"}
                {key === 'solar' && "Precise solar generation predictions with weather analysis"}
                {key === 'demand' && "Accurate demand forecasting for better planning"}
                {key === 'grid' && "AI-powered grid balancing and optimization"}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* <!-- slider --> */}
      <section className="relative bg-transparent grid">
        <div id="slider-1">
          <div className={`p-10 md-p-l10 flex justify-center items-center flex-column text-center ${currentSlide === 0 ? 'block' : 'hidden'}`}>
            <h2 className="white fs-l3 fw-900">Improve Grid Stability</h2>
            <p className="indigo-lightest fw-600 fs-m1 opacity-30 my-5">Minimize fluctuations and optimize energy distribution.</p>
          </div>
          <div className={`p-10 md-p-l10 flex justify-center items-center flex-column text-center ${currentSlide === 1 ? 'block' : 'hidden'}`}>
            <h2 className="white fs-l3 fw-900">Reduce Fossil Fuel Dependence</h2>
            <p className="indigo-lightest fw-600 fs-m1 opacity-30 my-5">Efficient forecasting lowers the need for backup power.</p>
          </div>
          <div className={`p-10 md-p-l10 flex justify-center items-center flex-column text-center ${currentSlide === 2 ? 'block' : 'hidden'}`}>
            <h2 className="white fs-l3 fw-900">Enhance Sustainability Goals</h2>
            <p className="indigo-lightest fw-600 fs-m1 opacity-30 my-5">Make data-driven decisions for a cleaner, greener energy future.</p>
          </div>
        </div>
        <ul className="absolute list-none w-full flex justify-between items-center top-1/2 transform -translate-y-1/2">
          <li>
            <button
              onClick={handlePrevClick}
              className="prev ml-10 rounded-full border border-indigo-lightest text-indigo-lightest bg-transparent flex justify-center items-center p-2 focus:outline-none"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
              </svg>
            </button>
          </li>
          <li>
            <button
              onClick={handleNextClick}
              className="next mr-10 rounded-full border border-indigo-lightest text-indigo-lightest bg-transparent flex justify-center items-center p-2 focus:outline-none"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </button>
          </li>
        </ul>
      </section>

      <footer className="text-center py-6 text-slate-400 mt-auto">
        <p className="flex items-center justify-center gap-2">
          Made with <span className="text-red-500">❤</span> at BHU
        </p>
      </footer>
    </div>
  );
}