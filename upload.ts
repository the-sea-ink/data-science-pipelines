import axios from 'axios';

export async function upload(file: File){
    const formData = new FormData();
    formData.append('file', file);
    let resp = await axios.post("/upload", formData, {
      headers: {
        'content-type': 'multipart/form-data'
      }
    });

    if (resp.status != 200){
      throw new Error(`Ran into error: http:${resp.status} ${resp.statusText} details:${resp.data}`);
    }

    return resp.data;
}
