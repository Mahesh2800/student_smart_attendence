import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getStudentPercentage } from '../../api/studentService'
import StudentCard from '../../components/StudentCard'
import LowAttendanceAlert from '../../components/LowAttendanceAlert'
import Loader from '../../components/Loader'
export default function StudentDashboard() { const { user } = useAuth(); const [data, setData] = useState(null); useEffect(() => { getStudentPercentage(user?.student_id || 1).then(({ data: payload }) => setData(payload)).catch(() => setData({ subjects: {}, overall: 0 })) }, [user]); const subjects = data ? Object.entries(data.subjects) : []; return <><div className="page-heading"><div><span className="eyebrow">STUDENT HUB</span><h1>Your attendance, at a glance.</h1><p>Know where you stand before it becomes a problem.</p></div><span className="date-chip">This term</span></div>{!data ? <Loader /> : <><LowAttendanceAlert count={subjects.filter(([, value]) => value < 75).length} /><div className="metric-grid">{subjects.map(([subject, percentage]) => <StudentCard key={subject} subject={subject} percentage={percentage} />)}<article className="metric-card total-card"><div className="card-kicker">OVERALL</div><div className="metric-value">{data.overall}%</div><p className="card-meta">Across eligible sessions</p></article></div></>}</> }
