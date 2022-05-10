import React, { Component } from 'react';

export default function Upload() {

    const [ file, setfile ] = React.useState<File>();

    const handlefile = (event: React.ChangeEvent<HTMLInputElement>) => {
        console.log(event.target.files);
        let currentfile = event.target.files;
        if (currentfile!=null) { setfile(currentfile[0] )
            console.log(currentfile[0]);
        }
      }
      
      const uploadFile = function (e: React.MouseEvent<HTMLSpanElement, MouseEvent>) {
        e.preventDefault()
        console.log(file)
        if (file) {
            console.log(file);
            const formData = new FormData();
            formData.append("file", file);
            formData.append("name", file.name);
            console.log(file.name);
            fetch(
                '/upload',
                {
                    method: 'POST',
                    body: formData,
                }
            )
                .then((response) => response.json())
                .then((result) => {
                    console.log('Success:', result);
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
        };

      };

    return(
        <div>
            <form>
                <div>
                    <label> Select File</label>
                    <input type='file' name='file' onChange={handlefile}/>

                </div>
                <button onClick={uploadFile}>Upload</button>
            </form>

        </div>
    )
}
