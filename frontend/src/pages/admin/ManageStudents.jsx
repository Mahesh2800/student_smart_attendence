import { useEffect, useState } from 'react'
import api from '../../api/axiosConfig'
import { CrudPage } from './ManageDepartments'
export default function ManageStudents() { const [items, setItems] = useState([]); useEffect(() => { api.get('/attendance/students/').then(({ data }) => setItems(data.results || data)).catch(() => {}) }, []); return <CrudPage title="Students" kicker="PEOPLE" description="Search the student directory and current section assignments." headers={['Roll number', 'Name', 'Department', 'Section']} rows={items.map((item) => [item.roll_no, item.name || item.username, item.department, item.current_section])} /> }
