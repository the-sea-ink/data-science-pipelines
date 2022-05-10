import React, { useEffect, useState } from 'react';

import CodeMirror from '@uiw/react-codemirror';
import { javascript } from '@codemirror/lang-javascript';
import { xml } from '@codemirror/lang-xml';
import { Language } from '@mui/icons-material';

interface Props {
  code: string,
  onCodeChange: (c: string) => void
}

export default function Coder(props: Props) {
  const [code, setCode] = React.useState<string>('');

  useEffect(() => {
    setCode(props.code);
  }, [props.code]);

  return (
    <CodeMirror
      value={code}
      extensions={[javascript({ jsx: true })]}

      onChange={(value, viewUpdate) => {
        var backendJson=JSON.stringify(value);
        setCode(JSON.parse(backendJson))
      }}
    />
  );
}
