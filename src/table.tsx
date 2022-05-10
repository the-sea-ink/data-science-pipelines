import React,{useEffect} from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';


export default function BasicTable() {
  const [ finalvals, setvals ] = React.useState<string[][]>([]);
  const [ loading, setLoading ] = React.useState<boolean>();

  var i:number=0;
  const load = function(){ 
    fetch( './newruns.csv' )
    .then( response => response.text() )
    .then( responseText => {
        const newtext = responseText.split(/[\n]+/)
        var vals:string[][] = []

        newtext.forEach(val => {
          // further split by each section by the CSV
          vals.push(val.split(','));
      })
      setvals(vals)
      setLoading(true)   
          })
          
        
};

// useEffect(() => {
//   console.log('hi')
//   fetch( './newruns.csv' )
//   .then( response => response.text() )
//   .then( responseText => {
//       // const newtext = responseText.split(/[\n]+/)
//       const newtext = responseText.split(/[\n]+/)
//       console.log(responseText)
//       var vals:string[][] = []

//       newtext.forEach(val => {
//         // further split by each section by the CSV
//         vals.push(val.split(','));
//         // vals.push(val.split(';'));

//     })
//     console.log(vals)
//     setvals(vals)
//     setLoading(true)   
//         })}, [])



  return (
    <div>
      
    <button onClick={ load }>load</button>
     {loading ? <div>                                  
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 650 }} aria-label="simple table">
        <TableHead>
          <TableRow>
          {finalvals[0].map((row,index) => (
            <TableCell key={index}>{row}</TableCell>))}
          </TableRow>
        </TableHead>
        {finalvals.slice(1).map((row,index) => (
        <TableBody>
            <TableRow
              sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
            >
              {row.map((row,index) => (
              <TableCell key={index} component="th" scope="row">
                {row}
              </TableCell>))}
            </TableRow>
         
        </TableBody> ))}
      </Table>
    </TableContainer>
      </div> : null}
    </div>
  );
}
