"use client";

import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import data from '../../data/mortgage_rate.json';

  const Page = () => {
    const chartRef = useRef(null);
    console.log(data);

    useEffect(() => {
      // Load data from JSON file
        // Parse the date strings into actual Date objects
        const parseDate = d3.timeParse('%Y-%m-%d');
        // data has two columns: date and rate
        const dates = data['date'].map(d => parseDate(d));
        const rates = data['rate'];
        console.log(dates);
        console.log(rates);
        // Set up chart dimensions
        const margin = { top: 20, right: 30, bottom: 30, left: 40 };
        const width = 600 - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        // Create SVG element
        console.log(chartRef.current);
        const svg = d3
          .select(chartRef.current)
          .append('svg')
          .attr('width', width + margin.left + margin.right)
          .attr('height', height + margin.top + margin.bottom)
          .append('g')
          .attr('transform', `translate(${margin.left},${margin.top})`);

        // Set up scales
        const x = d3
          .scaleTime()
          .domain(d3.extent(dates))
          .range([0, width]);

        const y = d3
          .scaleLinear()
          .domain([0, d3.max(rates)])
          .range([height, 0]);
          data
        // Set up line generator
        const line = d3
          .line()
          .x(d => x(dates))
          .y(d => y(rates));

        // Draw line chart
        svg
          .append('path')
          .datum(data)
          .attr('fill', 'none')
          .attr('stroke', 'steelblue')
          .attr('stroke-width', 1.5)
          .attr('d', line);

        // Add x-axis
        svg
          .append('g')
          .attr('transform', `translate(0,${height})`)
          .call(d3.axisBottom(x));

        // Add y-axis
        svg.append('g').call(d3.axisLeft(y));
    }, []);
    return <div ref={chartRef} ttt='a'></div>;
  };

  export default Page;