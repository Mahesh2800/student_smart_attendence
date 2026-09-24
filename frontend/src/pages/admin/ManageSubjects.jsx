import { useEffect, useState } from 'react'
import api from '../../api/axiosConfig'
import { CrudPage } from './ManageDepartments'
export default function ManageSubjects() { const [items, setItems] = useState([]); useEffect(() => { api.get('/attendance/subjects/').then(({ data }) => setItems(data.results || data)).catch(() => {}) }, []); return <CrudPage title="Subjects" kicker="CURRICULUM" description="Maintain the subject catalogue and its teaching context." headers={['Code', 'Subject', 'Credits', 'Semester']} rows={items.map((item) => [item.code, item.name, item.credits, item.semester])} /> }
