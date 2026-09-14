"use client"
import {CartesianGrid,Line,LineChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts'
import {EmptyState} from '../ui'
import {chronological,localTimestamp,metrics,type Metric,type RunSummary} from './history'
export default function QualityTrendChart({runs,metric}:{runs:RunSummary[];metric:Metric}) {
  if (!runs.some(run => run[metric] !== null)) return <EmptyState title="No applicable scores for this metric" description="This dimension is N/A for the loaded runs. Missing scores are not plotted as zero."/>
  return <div aria-label={`${metrics[metric]} score history; values also available in the run history table.`} role="region">
    <ResponsiveContainer width="100%" height={280} minWidth={0}>
      <LineChart data={chronological(runs)} margin={{top:15,right:20,bottom:10,left:0}} accessibilityLayer>
        <CartesianGrid stroke="#e1e7ed" strokeDasharray="3 3" vertical={false}/>
        <XAxis dataKey="created_at" tickFormatter={timestamp=>new Date(timestamp).toLocaleString('en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})} tick={{fontSize:10,fill:'#627485'}} minTickGap={35}/>
        <YAxis domain={[0,100]} ticks={[0,25,50,75,100]} tick={{fontSize:10,fill:'#627485'}} width={40}/>
        <Tooltip labelFormatter={timestamp=>localTimestamp(String(timestamp))} formatter={value=>[value==null?'N/A':Number(value).toFixed(2),metrics[metric]]}/>
        <Line type="linear" dataKey={metric} name={metrics[metric]} stroke="#087e8b" strokeWidth={2} dot={{r:3}} activeDot={{r:5}} connectNulls={false} isAnimationActive={false}/>
      </LineChart>
    </ResponsiveContainer>
    <p className="muted text-xs mt-2">Local execution time · score scale 0–100 · missing dimensions leave gaps.</p>
  </div>
}
