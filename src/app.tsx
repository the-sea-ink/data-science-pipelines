import React, { useState, useEffect, useCallback } from 'react';
import { styled } from '@mui/system';
import {
  Typography,
  List,
  IconButton,
  Drawer,
  Box,
  CssBaseline,
  Grid,
  Stack } from '@mui/material';

import ReactFlow, {
  addEdge,
  Controls,
  Background,
  Position,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  Connection,
  applyNodeChanges,
  applyEdgeChanges,
} from 'react-flow-renderer';
import dagre from 'dagre';

import AddBoxIcon from '@mui/icons-material/AddBox';
import Coder from "./codeMirror";

import {upload} from '../upload';

const Input = styled('input')({
  display: 'none',
});

export default function App() {
    const [code, setCode] = useState<string>('hello world');
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);

    function handleDrawerToggle(): boolean { return true };
    const drawerWidth = 48;

    function onCodeChange(c: string): void {
        setCode(c);
    }

    const onNodesChange = useCallback(
      (changes: NodeChange[]) => setNodes((ns: Node[]) => applyNodeChanges(changes, ns)),
      []
    );

    const onEdgesChange = useCallback(
      (changes: EdgeChange[]) => setEdges((es: Edge[]) => applyEdgeChanges(changes, es)),
      []
    );

    const onConnect = useCallback((connection: Connection) => setEdges((eds: Edge[]) => addEdge(connection, eds)), []);

    const nodeWidthPerLetter = 20;
    const nodeHeight = 36;

    const getLayoutedElements = (nodes: Node[], edges: Edge[], direction: string = 'horizontal') => {

      const dagreGraph = new dagre.graphlib.Graph();
      dagreGraph.setDefaultEdgeLabel(() => ({}));

      const isHorizontal = direction === 'horizontal';
      dagreGraph.setGraph({ rankdir: isHorizontal ? 'LR' : 'TB' });

      nodes.forEach( (n: Node) => {
        dagreGraph.setNode(n.id, { width: nodeWidthPerLetter * n.data.label.length , height: nodeHeight });
      });

      edges.forEach( (e: Edge) => {
        dagreGraph.setEdge(e.source, e.target);
      });

      dagre.layout(dagreGraph);

      return nodes.map( (el: Node) => {
        const nodeWithPosition = dagreGraph.node(el.id);
        el.targetPosition = isHorizontal ? Position.Left : Position.Top;
        el.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;

        // unfortunately we need this little hack to pass a slightly different position
        // to notify react flow about the change. Moreover we are shifting the dagre node position
        // (anchor=center center) to the top left so it matches the react flow node anchor point (top left).
        el.position = {
          x: nodeWithPosition.x - nodeWidthPerLetter * el.data.label.length / 2 + Math.random() / 1000,
          y: nodeWithPosition.y - nodeHeight / 2,
        };

        return el;
      });
    };

    return (
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <Box
          component="nav"
          sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
          aria-label="mailbox folders"
        >
          <Drawer
            variant="permanent"
            open={true}
            onClose={handleDrawerToggle}
            ModalProps={{
              keepMounted: true, // Better open performance on mobile.
            }}
            sx={{
              display: { xs: 'block' },
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
            }}
          >
            <Stack spacing={2}>
              <label htmlFor="icon-button-file">
                <Input accept='.py' id="icon-button-file" type="file" onChange={async (e) => {
                    e.preventDefault();
                    let target = (e.target as HTMLInputElement);
                    if (target.files?.length) {
                      let file = target.files?.item(0)!;
                      let resp = await upload(file);
                      console.log(resp);
                      setCode(resp.values.code);
                      setNodes(resp.values.nodes);
                      setEdges(resp.values.edges);
                    }
                  }}
                />
                <IconButton color="primary" aria-label="upload picture" component="span">
                  <AddBoxIcon />
                </IconButton>
              </label>

            </Stack>
          </Drawer>
        </Box>
        <Box
          component="main"
          sx={{ flexGrow: 1, p: 1, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
        >
          <Grid container spacing={1} columnSpacing={1}>
            <Grid item xs rowSpacing={1}>
              <Box sx={{ border: 1, height: '98vh' }}>
                <Coder code={code} onCodeChange={onCodeChange} />
              </Box>
            </Grid>
            <Grid item xs rowSpacing={1}>
              <Box sx={{ border: 1, height: '98vh' }}>
                <ReactFlow
                  nodes={getLayoutedElements(nodes, edges)}
                  edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  onConnect={onConnect}
                  snapToGrid={true}
                  snapGrid={[15, 15]}
                >
                  <Controls />
                  <Background color="#aaa" gap={16} />
                </ReactFlow>
              </Box>
            </Grid>
        </Grid>
        </Box>
      </Box>
    )
}
