import React, { Fragment } from 'react';
import ReactFlow, { Node, Edge } from 'react-flow-renderer';


const initialNodes: Node[] = [
  {
    id: '1',
    type: 'input',
    data: {
      label: 'Data Loading'
    },
    position: { x: 250, y: 0 },
  },
  {
    id: '2',
    data: {
      label: 'Data Profiling',
    },
    position: { x: 100, y: 100 },
  },
  {
    id: '3',
    data: {
      label: 'Missing Value Imputation',
    },
    position: { x: 400, y: 100 },
  },
  {
    id: '4',
    position: { x: 250, y: 200 },
    data: {
      label: 'Data Scaling',
    },
  },
  {
    id: '5',
    data: {
      label: 'Data Splitting',
    },
    position: { x: 250, y: 325 },
  },
  {
    id: '6',
    type: 'output',
    data: {
      label: 'output X',
    },
    position: { x: 100, y: 480 },
  },
  {
    id: '7',
    type: 'output',
    data: { label: 'output Y' },
    position: { x: 400, y: 450 },
  }
]

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2' },
  { id: 'e1-3', source: '1', target: '3' },
  {
    id: 'e3-4',
    source: '3',
    target: '4',
  },
  {
    id: 'e4-5',
    source: '4',
    target: '5',
  },
  {
    id: 'e5-6',
    source: '5',
    target: '6',
  },
  {
    id: 'e5-7',
    source: '5',
    target: '7',
  },
];

export { initialNodes, initialEdges };
