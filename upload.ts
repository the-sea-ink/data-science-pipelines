import axios from 'axios';

export async function upload(file: File, language: string){
    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', language);
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

export async function update(code: string, language: string){
    const formData = new FormData();
    formData.append('code', code);
    formData.append('language', language);
    let resp = await axios.post("/update", formData, {
      headers: {
      }
    });

    if (resp.status != 200){
      throw new Error(`Ran into error: http:${resp.status} ${resp.statusText} details:${resp.data}`);
    }

    return resp.data;
}
