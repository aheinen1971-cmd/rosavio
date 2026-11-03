"""Authenticated metadata lookup; token is confined to the gh subprocess."""
import json,os,re,subprocess

def get_release(tag,token):
 if not re.fullmatch(r'v\d+(?:\.\d+){1,3}-rosavio-linux-x64\.\d+',tag):raise ValueError('Invalid Linux release tag')
 if not token:raise ValueError('GitHub metadata token required')
 env={**os.environ,'GH_TOKEN':token}
 result=subprocess.run(['gh','api','repos/aheinen1971-cmd/rosavio/releases/tags/'+tag],env=env,capture_output=True,text=True)
 if result.returncode:raise RuntimeError('Authenticated Linux source metadata lookup failed')
 data=json.loads(result.stdout)
 if not isinstance(data,dict) or data.get('tag_name')!=tag or not isinstance(data.get('assets'),list):raise ValueError('Invalid Linux release metadata')
 return data
