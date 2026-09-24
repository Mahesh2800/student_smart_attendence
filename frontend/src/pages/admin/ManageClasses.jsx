import { useEffect, useState } from 'react'
import api from '../../api/axiosConfig'
import { CrudPage } from './ManageDepartments'
export default function ManageClasses() { const [items, setItems] = useState([]); useEffect(() => { api.get('/attendance/sections/').then(({ data }) => setItems(data.results || data)).catch(() => {}) }, []); return <CrudPage title="Classes" kicker="ACADEMIC MAP" description="Keep year, semester, and section assignments clear." headers={['Section', 'Year', 'Semester', 'Department']} rows={items.map((item) => [item.section_name, item.year, item.semester, item.department])} /> }
