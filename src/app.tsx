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
  DialogTitle,
  Dialog,
  InputLabel,
  MenuItem,
  FormControl,
  Stack } from '@mui/material';

import Select, { SelectChangeEvent } from '@mui/material/Select';


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

import {upload, update} from '../upload';

const Input = styled('input')({
  display: 'none',
});

export interface SimpleDialogProps {
  open: boolean;
  selectedValue: string;
  onClose: (value: string) => void;
}

function SimpleDialog(props: SimpleDialogProps) {
  const { onClose, selectedValue, open } = props;

  const handleClose = () => {
    onClose(selectedValue);
  };

  const handleChange = (event: SelectChangeEvent) => {
    onClose(event.target.value);
  };

  return (
    <Dialog onClose={handleClose} open={open}>
      <DialogTitle>Select Programming Language</DialogTitle>
      <Box sx={{ minWidth: 120 }}>
      <FormControl fullWidth>
        <InputLabel id="demo-simple-select-label">Language</InputLabel>
        <Select
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={props.selectedValue}
          label="Language"
          onChange={handleChange}
        >
          <MenuItem value={'python'}>Python</MenuItem>
          <MenuItem value={'r'}>R</MenuItem>
          <MenuItem value={'snakemake'}>snakemake</MenuItem>
        </Select>
      </FormControl>
    </Box>
    </Dialog>
  );
}

var globalChangesCounter = 0;

export default function App() {
    const [code, setCode] = useState<string>('hello world');
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [language, setLanguage] = useState<string>('');
    const [open, setOpen] = useState<boolean>(false);

    const handleChange = (event: SelectChangeEvent) => {
      setLanguage(event.target.value as string);
    };

    function handleDrawerToggle(): boolean { return true };
    const drawerWidth = 48;

    let lastChange = 0

    async function onCodeChange(c: string): Promise<void> {
        globalChangesCounter += 1;
        let localChangesCounter = globalChangesCounter;
        setTimeout(() => {
                if (globalChangesCounter == localChangesCounter) {
                    setCode(c);
                    upd(c);
                }
        },
            1000
        );

    }

    async function upd(c: string): Promise<void> {
      let resp = await update(c, language);
      console.log(resp);
      setNodes(resp.values.nodes);
      setEdges(resp.values.edges);
    }

    function onClose(l: string): void {
        setLanguage(l);
        setOpen(false);
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

    const getLayoutedElements = (nodes: Node[], edges: Edge[], direction: string = 'vertical') => {
      console.log(nodes, edges);
      const dagreGraph = new dagre.graphlib.Graph();
      dagreGraph.setDefaultEdgeLabel(() => ({}));

      const isHorizontal = direction === 'horizontal';
      dagreGraph.setGraph({ rankdir: isHorizontal ? 'LR' : 'TB' });

      nodes.forEach( (n: Node) => {
        dagreGraph.setNode(n.id, { width: nodeWidthPerLetter * (n.data.task ? n.data.label.length : 20) , height: nodeHeight });
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
          x: nodeWithPosition.x - nodeWidthPerLetter * (el.data.task ? el.data.label.length : 20) / 2 + Math.random() / 1000,
          y: nodeWithPosition.y - nodeHeight / 2,
        };

        return el;
      });
    };

    return <>
      <SimpleDialog open={open} selectedValue={language} onClose={onClose} />
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <Box
          component="main"
          sx={{ flexGrow: 1, p: 1, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
        >
          <Grid container spacing={1} columnSpacing={1}>
            <Grid item xs rowSpacing={1}>
              <Stack spacing={1}>
                <Stack spacing={1} direction="row">
                <label htmlFor="icon-button-file">
                  <Input accept='.py,.r,.snakefile' id="icon-button-file" type="file" onChange={async (e) => {
                      e.preventDefault();
                      function delay(s: number) {
                        return new Promise( resolve => setTimeout(resolve, 1000*s) );
                      }
                      let target = (e.target as HTMLInputElement);
                      if (target.files?.length) {
                        let file = target.files?.item(0)!;
                        if (language == '') {
                          setOpen(true);
                          while (language == '') {
                            delay(1);
                          }
                        }
                        let resp = await upload(file, language);
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
                <Box sx={{ minWidth: 120 }}>
                <FormControl fullWidth size="small">
                  <InputLabel id="demo-simple-select-label">Language</InputLabel>
                  <Select
                    labelId="demo-simple-select-label"
                    id="demo-simple-select"
                    value={language}
                    label="Language"
                    onChange={handleChange}
                  >
                    <MenuItem value={'python'}>Python</MenuItem>
                    <MenuItem value={'r'}>R</MenuItem>
                    <MenuItem value={'snakemake'}>snakemake</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              </Stack>
              <Box sx={{ border: 1, height: '92vh' }}>
                <Coder code={code} onCodeChange={onCodeChange} />
              </Box>
              </Stack>
            </Grid>
            <Grid item xs rowSpacing={1}>
              <Box sx={{ border: 1, height: '98vh', width: '50vw'}}>
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
    </>
}
